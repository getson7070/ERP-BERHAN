# erp/utils/jwt_helpers.py
from __future__ import annotations

from functools import wraps
from typing import Callable, Any

def require_jwt(optional: bool = False, fresh: bool = False) -> Callable:
    """
    Replacement for @jwt_required() that avoids importing flask_jwt_extended
    at module import time. It imports and validates inside the request.
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Import only when a request is actually being handled.
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=optional, fresh=fresh)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_jwt_claims() -> dict:
    """
    Lazy accessor to JWT claims (same as flask_jwt_extended.get_jwt()).
    """
    from flask_jwt_extended import get_jwt  # imported lazily
    return dict(get_jwt() or {})


def has_any_role(*needed: str) -> bool:
    """
    Role check against a 'roles' array in JWT claims (adjust if your claim key
    is different — e.g., 'permissions').
    """
    claims = get_jwt_claims()
    roles = set(claims.get("roles") or [])
    return any(r in roles for r in needed)
