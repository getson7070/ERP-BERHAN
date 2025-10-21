from __future__ import annotations
import fnmatch, time

_store = {}

def cache_set(key, value, ttl=None):
    exp = (time.time() + ttl) if ttl else None
    _store[key] = (value, exp)

def cache_get(key):
    v = _store.get(key)
    if not v: return None
    value, exp = v
    if exp and exp < time.time():
        _store.pop(key, None)
        return None
    return value

def cache_invalidate(pattern: str):
    for k in list(_store.keys()):
        if fnmatch.fnmatch(k, pattern):
            _store.pop(k, None)
