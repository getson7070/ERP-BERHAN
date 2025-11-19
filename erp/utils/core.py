"""Module: utils.py — shared helpers for auth, idempotency, and exports."""

from __future__ import annotations

import functools
import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Iterable

from flask import (
    Request,
    Response,
    abort,
    current_app,
    g,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required as _fl_login_required

from db import redis_client
from erp.metrics import RATE_LIMIT_REJECTIONS
from erp.security import require_login, require_roles

# Structured audit logging with hash chaining
try:
    from erp.audit import log_audit  # pragma: no cover - optional dependency
except Exception:  # pragma: no cover - fall back to no-op in minimal envs
    def log_audit(*_, **__):
        return None


# ----- Auth helpers -----

def hash_password(pw: str) -> str:
    """Return a salted hash (prefer Werkzeug, fallback to PBKDF2)."""
    try:
        from werkzeug.security import generate_password_hash
        return generate_password_hash(pw)
    except Exception:
        # PBKDF2-HMAC-SHA256 with random hex salt
        salt = os.urandom(16).hex()
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 600_000).hex()
        return f"pbkdf2_sha256${salt}${dk}"


def verify_password(pw: str, hashed: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed, pw)
    except Exception:
        if hashed.startswith("pbkdf2_sha256$"):
            _, salt, dk_hex = hashed.split("$", 2)
            calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 600_000).hex()
            return calc == dk_hex
        return False


# ----- Login/role/MFA gates -----

def login_required(fn):
    """
    Wrapper around Flask-Login's login_required.

    Older code imports erp.utils.login_required; this ensures all such views
    behave like real authenticated endpoints.
    """
    return _fl_login_required(fn)


# Role hierarchy: Admin > Manager > Staff
_RANKS = {"Admin": 3, "Manager": 2, "Staff": 1, None: 0}


def _current_role() -> str | None:
    """
    Determine the user's role:

    1. Prefer current_user.role (if present).
    2. Fall back to session["role"] for legacy/tests.
    """
    if current_user.is_authenticated:
        role = getattr(current_user, "role", None)
        if role:
            return role
    return session.get("role")


def has_permission(user_role: str | None, required_role: str | None) -> bool:
    """Return True if user_role >= required_role in the rank hierarchy."""
    return _RANKS.get(user_role, 0) >= _RANKS.get(required_role, 0)


def role_required(*roles):
    """
    Require at least one of the given roles.

    Example:
        @role_required("Manager", "Admin")
        def view():
            ...
    """
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            # Honour testing mode where login is disabled
            try:
                from flask import current_app

                if current_app.config.get("LOGIN_DISABLED"):
                    return fn(*a, **k)
            except Exception:
                pass

            user_role = _current_role()
            needed = max((_RANKS.get(r, 0) for r in roles), default=0)
            if _RANKS.get(user_role, 0) < needed:
                # Could also redirect to a dedicated "access denied" page
                return redirect(url_for("main.dashboard"), code=302)
            return fn(*a, **k)
        return wrapper
    return deco


# Alias some tests import
roles_required = role_required


def mfa_required(fn):
    """
    Enforce a simple MFA flag before allowing access.

    Assumes:
      * current_user.is_authenticated is already enforced (e.g. via login_required)
      * current_user may have an `mfa_enabled` boolean attribute
      * a successful MFA challenge sets session["mfa_verified"] = True
    """
    @functools.wraps(fn)
    def wrapper(*a, **k):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"), code=302)

        mfa_enabled = getattr(current_user, "mfa_enabled", False)
        if mfa_enabled and not session.get("mfa_verified"):
            # redirect to an MFA challenge view (you implement this route)
            return redirect(url_for("auth.mfa_challenge"), code=302)

        return fn(*a, **k)
    return wrapper


# ----- Idempotency helpers -----

def idempotency_key_required(fn):
    """Require Idempotency-Key header to be present; 400 if missing."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        if not request.headers.get("Idempotency-Key"):
            abort(400, "Missing Idempotency-Key")
        return fn(*a, **k)
    return wrapper


def idempotent(fn):
    """Prevent duplicate processing when Idempotency-Key repeats; 409 on repeat."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return fn(*a, **k)
        cache_key = f"idemp:{key}"
        if redis_client.get(cache_key):
            RATE_LIMIT_REJECTIONS.inc()
            abort(409, "Duplicate request")
        redis_client.set(cache_key, "1")
        return fn(*a, **k)
    return wrapper


# ----- Dead letter recording -----

def dead_letter_handler(*, sender=None, task_id=None, exception=None, args=(), kwargs=None, **_):
    """Compatible signature with Celery's task_failure signal in tests."""
    payload = {
        "task": getattr(sender, "name", str(sender)),
        "task_id": task_id,
        "error": str(exception),
        "args": list(args),
        "kwargs": kwargs or {},
    }
    redis_client.rpush("dead_letter", json.dumps(payload))


# ---- Celery task idempotency (used by retention/reporting tests) ----

def task_idempotent(fn):
    """Prevent duplicate execution of Celery tasks based on an idempotency key."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        key = k.get("idempotency_key") or k.get("task_id") or k.get("key")
        if not key:
            return fn(*a, **k)
        ck = f"task_idemp:{fn.__name__}:{key}"
        if redis_client.get(ck):
            RATE_LIMIT_REJECTIONS.inc()
            raise RuntimeError("Duplicate task")
        redis_client.set(ck, "1")
        return fn(*a, **k)
    return wrapper


# ---- Small sanitizer expected by tenders workflow tests ----

def sanitize_direction(value: str | None, default: str = "asc") -> str:
    v = (value or "").lower()
    return "desc" if v == "desc" else "asc"


def sanitize_sort(value: str | None, allowed=None, default="created_at") -> str:
    allowed = set(allowed or ["created_at", "name", "status", "id"])
    v = (value or "").lower()
    return v if v in allowed else default


def stream_export(rows: Iterable[Iterable[object] | object], filename: str = "export.csv") -> Response:
    """Stream a simple CSV export from an iterable of rows."""
    def _line(r):
        if isinstance(r, (list, tuple)):
            return ",".join(map(str, r))
        return str(r)

    body = "\n".join(_line(r) for r in rows)
    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def resolve_org_id(default: int = 1, req: Request | None = None) -> int:
    """Determine the active organisation id for the current request context."""

    if hasattr(g, "org_id"):
        try:
            return int(getattr(g, "org_id"))
        except (TypeError, ValueError):
            current_app.logger.debug("g.org_id invalid; falling back to request context")

    req = req or request
    if req is not None:
        candidate = req.args.get("org_id") or req.headers.get("X-Org-Id")
        if candidate:
            try:
                return int(candidate)
            except (TypeError, ValueError):
                current_app.logger.warning("Invalid org_id %s; using default", candidate)

    try:
        stored = session.get("org_id")
        if stored is not None:
            return int(stored)
    except (TypeError, ValueError):
        current_app.logger.debug("Session org_id invalid; defaulting")

    fallback = current_app.config.get("DEFAULT_ORG_ID", default)
    return int(fallback)
    return int(default)

def utility_function():
    """Autogenerated docstring (audit). Describe purpose, params, and return value."""
    return "Utility result"


__all__ = [
    "hash_password",
    "verify_password",
    "login_required",
    "role_required",
    "roles_required",
    "mfa_required",
    "has_permission",
    "idempotency_key_required",
    "idempotent",
    "dead_letter_handler",
    "task_idempotent",
    "sanitize_direction",
    "sanitize_sort",
    "stream_export",
    "resolve_org_id",
    "utc_now",
    "utility_function",
    "require_login",
    "require_roles",
]
