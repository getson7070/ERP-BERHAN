from time import time
from threading import RLock
from typing import Any, Optional, Tuple, Dict

# Simple in-memory cache with optional TTL and basic metrics.
# Thread-safe enough for tests / dev; swap for Redis/Memcached in prod.

_CACHE: Dict[str, Tuple[Any, Optional[float]]] = {}
_CACHE_LOCK = RLock()

# Metrics
CACHE_HITS: int = 0
CACHE_MISSES: int = 0


def init_cache() -> None:
    """Reset the in-memory cache and metrics (used by tests)."""
    global _CACHE, CACHE_HITS, CACHE_MISSES
    with _CACHE_LOCK:
        _CACHE = {}
        CACHE_HITS = 0
        CACHE_MISSES = 0


def cache_set(key: str, value: Any, ttl: Optional[float] = None) -> Any:
    """Set key to value with optional TTL (seconds)."""
    expires = (time() + float(ttl)) if ttl else None
    with _CACHE_LOCK:
        _CACHE[key] = (value, expires)
    return value


def cache_get(key: str, default: Any = None) -> Any:
    """Get key or default; updates hit/miss metrics; drops expired entries."""
    global CACHE_HITS, CACHE_MISSES
    now = time()
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            CACHE_MISSES += 1
            return default

        value, expires = entry
        if expires is not None and expires < now:
            # expired -> treat as miss and remove
            _CACHE.pop(key, None)
            CACHE_MISSES += 1
            return default

        CACHE_HITS += 1
        return value


def cache_invalidate(key: Optional[str] = None) -> int:
    """
    Invalidate a specific key, or clear all if key is None.
    Returns number of keys removed (0/1 for specific-key case).
    """
    with _CACHE_LOCK:
        if key is None:
            count = len(_CACHE)
            _CACHE.clear()
            return count
        return 1 if _CACHE.pop(key, None) is not None else 0


def CACHE_HIT_RATE() -> float:
    """Return hit rate as a float in [0.0, 1.0]."""
    total = CACHE_HITS + CACHE_MISSES
    return (CACHE_HITS / total) if total else 0.0


__all__ = [
    "init_cache",
    "cache_set",
    "cache_get",
    "cache_invalidate",
    "CACHE_HITS",
    "CACHE_MISSES",
    "CACHE_HIT_RATE",
]
