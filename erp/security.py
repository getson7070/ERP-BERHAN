from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional, TypeVar
import os  # kept for future expansion / compatibility

from flask import abort, redirect, request, url_for

try:  # Flask-Login is the primary auth backend
    from flask_login import current_user  # type: ignore
except Exception:  # pragma: no cover - defensive fallback
    current_user = None  # type: ignore[assignment]

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Core helpers: current user and roles
# ---------------------------------------------------------------------------

def _get_current_user() -> Any:
    """Return the current authenticated user object or None.

    Uses Flask-Login's ``current_user`` if available.
    """
    if current_user is None:
        return None
    try:
        # current_user is a LocalProxy in Flask-Login
        return current_user
    except Exception:  # pragma: no cover - defensive
        return None


def _get_user_role_names(user: Any) -> set[str]:
    """Extract a set of role names from the user object (lowercased).

    Supports both:
    - user.roles relationship with .name
    - fallback attributes like user.role or user.role_name
    """
    roles: set[str] = set()
    if not user:
        return roles

    # Relationship: user.roles -> [Role(name=...)]
    rel = getattr(user, "roles", None)
    if rel is not None:
        try:
            for r in rel:
                name = getattr(r, "name", None)
                if name:
                    roles.add(str(name).lower())
        except TypeError:
            # if roles is not iterable, ignore
            pass

    # Fallback fields
    for attr in ("role", "role_name"):
        val = getattr(user, attr, None)
        if isinstance(val, str):
            roles.add(val.lower())

    return roles


# ---------------------------------------------------------------------------
# Decorators: require_login / require_roles
# ---------------------------------------------------------------------------

def require_login(fn: F) -> F:
    """Decorator that requires an authenticated user.

    For HTML requests, redirects to the login page;
    for JSON/API requests, returns HTTP 401.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        user = _get_current_user()
        is_auth = bool(user and getattr(user, "is_authenticated", False))

        if not is_auth:
            # Heuristic: JSON-only -> API, otherwise treat as browser
            accepts_json = request.accept_mimetypes.accept_json
            accepts_html = request.accept_mimetypes.accept_html

            if accepts_json and not accepts_html:
                abort(401)
            return redirect(url_for("auth.login", next=request.url))

        return fn(*args, **kwargs)

    return wrapper  # type: ignore[misc]


def require_roles(*role_names: str) -> Callable[[F], F]:
    """Decorator enforcing that the user has at least one of the given roles.

    Example:
        @require_roles("admin", "finance")
        def post_journal(): ...
    """

    # Normalize role names to lowercase to support case-insensitive checks
    normalized = {r.strip().lower() for r in role_names if r and r.strip()}

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            user = _get_current_user()
            is_auth = bool(user and getattr(user, "is_authenticated", False))

            if not is_auth:
                accepts_json = request.accept_mimetypes.accept_json
                accepts_html = request.accept_mimetypes.accept_html
                if accepts_json and not accepts_html:
                    abort(401)
                return redirect(url_for("auth.login", next=request.url))

            if normalized:
                user_roles = _get_user_role_names(user)
                if not (user_roles & normalized):
                    abort(403)

            return fn(*args, **kwargs)

        return wrapper  # type: ignore[misc]

    return decorator


# ---------------------------------------------------------------------------
# Optional MFA decorator (kept simple to avoid breaking existing flows)
# ---------------------------------------------------------------------------

def mfa_required(fn: F) -> F:
    """Require that the user has passed MFA.

    This assumes the user object has a boolean attribute ``mfa_verified``
    or similar. If not present, MFA is treated as satisfied.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        user = _get_current_user()
        is_auth = bool(user and getattr(user, "is_authenticated", False))

        if not is_auth:
            accepts_json = request.accept_mimetypes.accept_json
            accepts_html = request.accept_mimetypes.accept_html
            if accepts_json and not accepts_html:
                abort(401)
            return redirect(url_for("auth.login", next=request.url))

        # If the app defines a stricter check, honour it; otherwise allow.
        mfa_ok = getattr(user, "mfa_verified", True)
        if not mfa_ok:
            # You can replace this with a dedicated MFA route in your app.
            abort(403)

        return fn(*args, **kwargs)

    return wrapper  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Existing cookie/CSP/HSTS hardening
# ---------------------------------------------------------------------------

def apply_security(app) -> None:
    """Harden cookies, enable CSP/HSTS if Flask-Talisman is available."""
    # Core cookies
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("REMEMBER_COOKIE_SECURE", True)
    app.config.setdefault("REMEMBER_COOKIE_HTTPONLY", True)

    # Basic CSP/HSTS via Talisman if installed
    try:
        from talisman import Talisman  # pip: flask-talisman or talisman (alias)
    except Exception:
        try:
            from flask_talisman import Talisman  # legacy pkg name
        except Exception:
            Talisman = None

    if Talisman:
        csp = {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'", "data:"],
            "connect-src": ["'self'"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'self'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
        }
        Talisman(
            app,
            content_security_policy=csp,
            force_https=False,  # set True behind a TLS-terminating proxy
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
        )


__all__ = [
    "require_login",
    "require_roles",
    "mfa_required",
    "apply_security",
]
