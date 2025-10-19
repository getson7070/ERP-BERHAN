from __future__ import annotations
import time
from threading import RLock
from typing import Any, Optional

__all__ = ["cache_set", "cache_get", "cache_invalidate"]

# Simple in-memory store: key -> (value, expires_at or None)
_STORE: dict[str, tuple[Any, Optional[float]]] = {}
_LOCK = RLock()

def _now() -> float:
    return time.time()

def _expired(expires_at: Optional[float]) -> bool:
    return expires_at is not None and _now() >= expires_at

def cache_set(key: str, value: Any, ttl: Optional[float] = None) -> None:
    """Set a value. If ttl (seconds) is provided, it will expire after ttl."""
    expires_at = (_now() + float(ttl)) if ttl else None
    with _LOCK:
        _STORE[str(key)] = (value, expires_at)

def cache_get(key: str, default: Any = None) -> Any:
    """Get a value or default if missing/expired."""
    k = str(key)
    with _LOCK:
        item = _STORE.get(k)
        if item is None:
            return default
        value, expires_at = item
        if _expired(expires_at):
            # drop and behave as missing
            _STORE.pop(k, None)
            return default
        return value

def cache_invalidate(*keys: str, prefix: Optional[str] = None) -> int:
    """
    Invalidate cache entries.
      - cache_invalidate("k1", "k2") removes specific keys.
      - cache_invalidate(prefix="user:") removes keys starting with that prefix.
      - cache_invalidate() (no args) clears the entire cache.
    Returns the number of removed entries.
    """
    removed = 0
    with _LOCK:
        # Remove explicit keys
        for k in keys or ():
            if _STORE.pop(str(k), None) is not None:
                removed += 1

        # Remove by prefix
        if prefix is not None:
            p = str(prefix)
            for k in list(_STORE.keys()):
                if k.startswith(p):
                    _STORE.pop(k, None)
                    removed += 1

        # If no keys and no prefix: clear all
        if not keys and prefix is None:
            removed = len(_STORE)
            _STORE.clear()

    return removed
