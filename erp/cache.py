from typing import Any, Optional

_CACHE: dict[str, Any] = {}
CACHE_HITS: int = 0
CACHE_MISSES: int = 0

def init_cache() -> None:
    global _CACHE, CACHE_HITS, CACHE_MISSES
    _CACHE = {}
    CACHE_HITS = 0
    CACHE_MISSES = 0

def cache_get(key: str) -> Optional[Any]:
    global CACHE_HITS, CACHE_MISSES
    if key in _CACHE:
        CACHE_HITS += 1
        return _CACHE[key]
    CACHE_MISSES += 1
    return None

def cache_set(key: str, value: Any) -> None:
    _CACHE[key] = value

def cache_invalidate(prefix: str | None = None) -> None:
    if not prefix:
        _CACHE.clear()
        return
    ks = [k for k in _CACHE.keys() if k.startswith(prefix)]
    for k in ks:
        _CACHE.pop(k, None)
