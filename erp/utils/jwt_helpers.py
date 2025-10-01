from __future__ import annotations

from typing import Any, Optional


def verify_jwt_in_request_if_present() -> bool:
    """
    Verify JWT only if the request actually carries one.
    Returns True if a valid JWT was present, False if not provided.
    Will raise if a token is provided but invalid/expired.
    """
    try:
        from flask import request

        authz = request.headers.get("Authorization", "")
        if not authz and "access_token" not in request.args:
            return False

        from flask_jwt_extended import verify_jwt_in_request

        verify_jwt_in_request()
        return True
    except Exception:
        # Let callers choose to handle/ignore; returning False keeps routes lenient.
        return False


def get_current_user_safe() -> Optional[Any]:
    """
    Safely access current_user only when a JWT/request context exists.
    Returns None if there's no valid request/JWT context.
    """
    try:
        from flask_jwt_extended import current_user  # local import to avoid global LocalProxy at import time

        return current_user  # may still be a LocalProxy but only inside a valid request ctx
    except Exception:
        return None
