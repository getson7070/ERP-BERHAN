"""
Minimal in-memory cache with counters used by tests.
"""
from __future__ import annotations
from time import time

_cache: dict[str, tuple[float | None, object]] = {}

CACHE_HITS = 0
CACHE_MISSES = 0

def init_cache() -> None:
    global _cache, CACHE_HITS, CACHE_MISSES
    _cache = {}
    CACHE_HITS = 0
    CACHE_MISSES = 0

def cache_set(key: str, value: object, ttl_seconds: float | None = None) -> None:
    expires = None if ttl_seconds is None else (time() + float(ttl_seconds))
    _cache[key] = (expires, value)

def cache_get(key: str):
    global CACHE_HITS, CACHE_MISSES
    item = _cache.get(key)
    if not item:
        CACHE_MISSES += 1
        return None
    expires, value = item
    if expires is not None and time() > expires:
        # expired
        del _cache[key]
        CACHE_MISSES += 1
        return None
    CACHE_HITS += 1
    return value

def CACHE_HIT_RATE() -> float:
    total = CACHE_HITS + CACHE_MISSES
    return (CACHE_HITS / total) if total else 0.0