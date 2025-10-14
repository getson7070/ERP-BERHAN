from functools import wraps
from flask import abort, request
from flask_login import current_user

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if roles and getattr(current_user, "role", None) not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def device_authorized():
    # Stub: implement your own logic (e.g., check device ID cookie or user agent/IP allowlist)
    # Return True/False
    return True
