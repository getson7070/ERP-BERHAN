import time
import threading

try:
    from prometheus_client import Gauge  # type: ignore
except Exception:  # pragma: no cover
    class Gauge:
        def __init__(self, *_a, **_k): self.value = 0
        def set(self, v): self.value = v
        def inc(self, v=1): self.value = getattr(self, "value", 0) + v

_lock = threading.RLock()
_store = {}

CACHE_HITS = Gauge("cache_hits", "Cache hits")
CACHE_MISSES = Gauge("cache_misses", "Cache misses")
CACHE_SIZE = Gauge("cache_size", "Cache size items")

def _gc():
    now = time.time()
    ttl_keys = [k for k, (v, exp) in _store.items() if exp is not None and exp <= now]
    for k in ttl_keys:
        _store.pop(k, None)
    CACHE_SIZE.set(len(_store))

def cache_get(key):
    with _lock:
        _gc()
        if key in _store:
            val, exp = _store[key]
            CACHE_HITS.inc(1)
            return val
        CACHE_MISSES.inc(1)
        return None

def cache_set(key, value, ttl=None):
    with _lock:
        exp = time.time() + ttl if ttl else None
        _store[key] = (value, exp)
        _gc()
        return True

def cache_clear():
    with _lock:
        _store.clear()
        _gc()
