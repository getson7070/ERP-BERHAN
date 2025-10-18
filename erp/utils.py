import functools, hashlib
from typing import Any, Callable

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def has_permission(user: Any, permission: str) -> bool:
    role = getattr(user, 'role', None) or (user.get('role') if isinstance(user, dict) else None)
    if role == 'admin': return True
    perms = getattr(user, 'permissions', None) or (user.get('permissions') if isinstance(user, dict) else [])
    return permission in set(perms or [])

_IDEMP_KEYS: set[str] = set()
def idempotency_key_required(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = kwargs.pop('idempotency_key', None) or (args[0] if args else None)
        if key and key in _IDEMP_KEYS:
            raise RuntimeError('Duplicate idempotency key')
        if key: _IDEMP_KEYS.add(key)
        return func(*args, **kwargs)
    return wrapper
