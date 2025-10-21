from time import time
from threading import RLock
from typing import Any, Optional, Tuple, Dict
import fnmatch

_CACHE: Dict[str, Tuple[Any, Optional[float]]] = {}
_CACHE_LOCK = RLock()

CACHE_HITS: int = 0
CACHE_MISSES: int = 0

def init_cache(app: Any = None) -> None:   # accept optional app
    global _CACHE, CACHE_HITS, CACHE_MISSES
    with _CACHE_LOCK:
        _CACHE = {}
        CACHE_HITS = 0
        CACHE_MISSES = 0

def cache_set(key: str, value: Any, ttl: Optional[float] = None) -> Any:
    expires = (time() + float(ttl)) if ttl else None
    with _CACHE_LOCK:
        _CACHE[key] = (value, expires)
    return value

def cache_get(key: str, default: Any = None) -> Any:
    global CACHE_HITS, CACHE_MISSES
    now = time()
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            CACHE_MISSES += 1
            return default
        value, expires = entry
        if expires is not None and expires < now:
            _CACHE.pop(key, None)
            CACHE_MISSES += 1
            return default
        CACHE_HITS += 1
        return value

def cache_invalidate(key: Optional[str] = None) -> int:
    with _CACHE_LOCK:
        if key is None:
            n = len(_CACHE); _CACHE.clear(); return n
        # support wildcards like "ns:*"
        if any(ch in ( "*", "?" ) for ch in key):
            keys = [k for k in list(_CACHE.keys()) if fnmatch.fnmatch(k, key)]
            for k in keys: _CACHE.pop(k, None)
            return len(keys)
        return 1 if _CACHE.pop(key, None) is not None else 0

def CACHE_HIT_RATE() -> float:
    total = CACHE_HITS + CACHE_MISSES
    return (CACHE_HITS / total) if total else 0.0

__all__ = [
    "init_cache", "cache_set", "cache_get", "cache_invalidate",
    "CACHE_HITS", "CACHE_MISSES", "CACHE_HIT_RATE",
]
