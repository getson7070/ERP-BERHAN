"""Dynamic RBAC engine and decorators."""

from functools import wraps
from flask import abort
from flask_login import current_user

def has_permission(permission_name: str) -> bool:
    """
    Dynamic RBAC check: True if user has role granting permission.
    Defaults False for unauth/unknown.
    """
    if not current_user.is_authenticated:
        return False
    # Integrates with user.has_permission (from models.user.py)
    return current_user.has_permission(permission_name.lower())

def require_permission(permission: str):
    """Decorator for route protection (abort 403 if no perm)."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator