# erp/utils/__init__.py
"""Utility helpers shared across ERP modules."""

from __future__ import annotations

from datetime import UTC, datetime
import functools

from flask import Request, current_app, redirect, request, session, url_for
from flask_login import current_user, login_required as _fl_login_required


# ---- Auth guards (mirrors legacy utils.py to keep imports stable) ----

def login_required(fn):  # type: ignore
    return _fl_login_required(fn)


_RANKS = {"Admin": 3, "Manager": 2, "Staff": 1, None: 0}


def _current_role():
    if current_user.is_authenticated:
        role = getattr(current_user, "role", None)
        if role:
            return role
    return session.get("role")


def role_required(*roles):  # type: ignore
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            # testing mode bypass
            try:
                if current_app.config.get("LOGIN_DISABLED"):
                    return fn(*a, **k)
            except Exception:
                pass

            user_role = _current_role()
            needed = max((_RANKS.get(r, 0) for r in roles), default=0)
            if _RANKS.get(user_role, 0) < needed:
                return redirect(url_for("main.dashboard"), code=302)
            return fn(*a, **k)

        return wrapper

    return deco


def mfa_required(fn):  # pragma: no cover - compatibility shim
    return fn


def idempotent(fn):  # pragma: no cover - compatibility shim
    return fn


def idempotency_key_required(fn):  # pragma: no cover - compatibility shim
    return fn


def has_permission(*_, **__):  # pragma: no cover - compatibility shim
    return True


def utc_now() -> datetime:
    """Return an explicit UTC timestamp for database fields and events."""

    return datetime.now(UTC)


def resolve_org_id(default: int = 1, req: Request | None = None) -> int:
    """Determine the active organisation id for the current request.

    The upgraded blueprints accept an ``org_id`` query parameter, fall back to
    a value stored in the session, and finally to the provided default.  The
    helper is deliberately defensive—if parsing fails it logs a warning and
    returns the default instead of raising, keeping endpoints predictable.
    """

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
    return int(default)


__all__ = ["resolve_org_id", "utc_now"]


