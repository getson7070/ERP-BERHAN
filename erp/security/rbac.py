from functools import wraps
from flask import abort
from flask_login import current_user

def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            user_roles = getattr(current_user, "roles", []) or []
            if not any(r in user_roles for r in roles):
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
