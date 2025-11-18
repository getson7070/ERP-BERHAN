from __future__ import annotations

from typing import Callable, TypeVar, Any
import os
from functools import wraps

# ---------------------------------------------------------------------------
# User context resolution (flask-security first, then flask-login fallback)
# ---------------------------------------------------------------------------

try:
    from flask_security import current_user as _current_user  # type: ignore
except Exception:  # pragma: no cover - only hit if flask_security isn't installed
    try:
        from flask_login import current_user as _current_user  # type: ignore
    except Exception:  # pragma: no cover - only hit if neither is installed
        _current_user = None  # type: ignore

F = TypeVar("F", bound=Callable[..., Any])


def require_login(func: F) -> F:
    """
    Decorator: require an authenticated user.
    Returns 401 if there is no authenticated user.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Local import avoids circulars if Flask app imports security early
        from flask import abort

        if _current_user is None or not getattr(_current_user, "is_authenticated", False):
            abort(401)
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def require_roles(*role_names: str) -> Callable[[F], F]:
    """
    Decorator: require that the current user has AT LEAST ONE of the given role names.

    Usage:

        @require_roles("admin", "finance")
        def some_view(...):
            ...

    - Returns 401 if not authenticated
    - Returns 403 if authenticated but none of the required roles are present
    """
    normalized = {r.strip() for r in role_names if r and r.strip()}

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from flask import abort

            if _current_user is None or not getattr(_current_user, "is_authenticated", False):
                abort(401)

            # Collect role names from current_user.roles (if present)
            user_roles_attr = getattr(_current_user, "roles", None)
            user_role_names: set[str] = set()

            if user_roles_attr:
                # Works for both list-like objects and SQLAlchemy relationship collections
                for r in user_roles_attr:
                    name = getattr(r, "name", None)
                    if isinstance(name, str):
                        user_role_names.add(name)

            # If there are no required roles configured, treat as "authenticated only"
            if normalized and not (user_role_names & normalized):
                abort(403)

            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# HTTP / cookie / CSP hardening
# ---------------------------------------------------------------------------

def apply_security(app) -> None:
    """
    Harden cookies and, if Flask-Talisman (or talisman) is available, enable
    a sane default CSP and HSTS.

    This function is intentionally side-effectful on the Flask app config and
    should be called from create_app().
    """
    # Core cookies
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("REMEMBER_COOKIE_SECURE", True)
    app.config.setdefault("REMEMBER_COOKIE_HTTPONLY", True)

    # Basic CSP/HSTS via Talisman if installed
    try:
        from talisman import Talisman  # pip: flask-talisman or talisman (alias)  # type: ignore
    except Exception:
        try:
            from flask_talisman import Talisman  # legacy pkg name  # type: ignore
        except Exception:
            Talisman = None  # type: ignore

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
            force_https=False,  # behind proxies this should be True with proper proxy headers
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
        )
