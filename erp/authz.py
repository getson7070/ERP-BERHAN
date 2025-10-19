
from __future__ import annotations
from functools import wraps
from flask import g, request, jsonify
from typing import Iterable, Callable, Any, Set

try:
    from .utils import has_permission as _has_perm
except Exception:
    def _has_perm(user: Any, permission: str) -> bool:  # pragma: no cover
        perms = getattr(user, "permissions", []) or []
        return permission in set(perms)

def require_permissions(required: Iterable[str] | Set[str]) -> Callable:
    required_set = set(required)
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None) or getattr(request, "user", None)
            if not user:
                return jsonify(error="unauthenticated"), 401
            missing = [p for p in required_set if not _has_perm(user, p)]
            if missing:
                return jsonify(error="forbidden", missing=missing), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


