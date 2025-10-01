# erp/utils.py
from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable, Any, Dict, List

from flask import jsonify, request

# NOTE:
# We intentionally DO NOT import from flask_jwt_extended at module import time.
# Each decorator imports what it needs inside the request handler so that
# no LocalProxy objects are created before eventlet monkey patching occurs.


def _json_error(status_code: int, message: str, extra: Dict[str, Any] | None = None):
    payload = {"error": message, "status": status_code}
    if extra:
        payload.update(extra)
    return jsonify(payload), status_code


def login_required(fn: Callable) -> Callable:
    """
    Require a valid JWT on the request.
    Equivalent to using flask_jwt_extended.verify_jwt_in_request() but
    kept here to avoid importing JWT at module load time.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper


def mfa_required(fn: Callable) -> Callable:
    """
    Require MFA. We accept either:
      - a boolean "mfa": true claim, OR
      - an "amr" (Authentication Methods Reference) array containing "mfa".
    If absent, return 401.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        verify_jwt_in_request()
        claims = get_jwt() or {}
        # Common patterns for indicating MFA in JWTs
        mfa_ok = bool(claims.get("mfa"))
        amr = claims.get("amr")
        if isinstance(amr, (list, tuple)) and "mfa" in amr:
            mfa_ok = True

        if not mfa_ok:
            return _json_error(401, "Multi-factor authentication required")
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*required_roles: Iterable[str]) -> Callable:
    """
    Require that the JWT 'roles' claim contains ALL of the roles passed.
    Example:
        @roles_required("admin", "manager")
        def view(): ...
    Returns 403 if insufficient.
    """
    # Normalize tuple-of-iterables/strings into a flat set of strings
    needed: List[str] = []
    for r in required_roles:
        if isinstance(r, str):
            needed.append(r)
        else:
            needed.extend([str(x) for x in r])

    needed_set = set(needed)

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request, get_jwt
            verify_jwt_in_request()
            claims = get_jwt() or {}
            roles = claims.get("roles", [])
            if isinstance(roles, str):
                roles_list = [roles]
            elif isinstance(roles, (list, tuple, set)):
                roles_list = list(roles)
            else:
                roles_list = []

            if not needed_set.issubset(set(roles_list)):
                return _json_error(403, "Insufficient role", {"required": sorted(needed_set)})

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def optional_jwt(fn: Callable) -> Callable:
    """
    Allow a route to work with or without a JWT. If present, it will be verified.
    Useful for public endpoints that behave slightly differently when authenticated.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, exceptions
        try:
            # Only verify if an Authorization header exists
            auth_hdr = request.headers.get("Authorization")
            if auth_hdr:
                verify_jwt_in_request()
        except exceptions.NoAuthorizationError:
            # Proceed unauthenticated
            pass
        return fn(*args, **kwargs)
    return wrapper
