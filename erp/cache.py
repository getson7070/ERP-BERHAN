from __future__ import annotations
import time
from threading import RLock
from typing import Any, Optional

__all__ = [
    "cache_set", "cache_get", "cache_invalidate",
    "CACHE_HITS", "CACHE_MISSES", "CACHE_SETS", "CACHE_INVALIDATIONS",
    "CACHE_SIZE", "CACHE_HIT_RATE",
]

# --- Prometheus metrics (with safe fallbacks) ---
try:
    from prometheus_client import Counter, Gauge  # type: ignore
except Exception:  # pragma: no cover
    class _NoopMetric:
        def inc(self, *a, **k): pass
        def set(self, *a, **k): pass
    def Counter(*a, **k):  # type: ignore
        return _NoopMetric()
    def Gauge(*a, **k):  # type: ignore
        return _NoopMetric()

# Simple names (tests often grep these in /metrics)
CACHE_HITS = Counter("cache_hits", "Number of cache hits")
CACHE_MISSES = Counter("cache_misses", "Number of cache misses")
CACHE_SETS = Counter("cache_sets", "Number of cache sets")
CACHE_INVALIDATIONS = Counter("cache_invalidations", "Number of cache invalidations")
CACHE_SIZE = Gauge("cache_size", "Current number of keys in cache")
CACHE_HIT_RATE = Gauge("cache_hit_rate", "Ratio of cache hits to total lookups (0..1)")

# Back-compat singulars just in case
CACHE_HIT = CACHE_HITS
CACHE_MISS = CACHE_MISSES

# --- Store ---
_STORE: dict[str, tuple[Any, Optional[float]]] = {}
_LOCK = RLock()

# Track lookups so we can compute hit-rate without peeking inside prometheus objects
_LOOKUPS_HITS = 0
_LOOKUPS_MISSES = 0

def _now() -> float:
    return time.time()

def _expired(expires_at: Optional[float]) -> bool:
    return expires_at is not None and _now() >= expires_at

def _update_size_gauge() -> None:
    try:
        CACHE_SIZE.set(len(_STORE))
    except Exception:
        pass

def _update_hit_rate_gauge() -> None:
    total = _LOOKUPS_HITS + _LOOKUPS_MISSES
    rate = (_LOOKUPS_HITS / total) if total else 0.0
    try:
        CACHE_HIT_RATE.set(rate)
    except Exception:
        pass

def cache_set(key: str, value: Any, ttl: Optional[float] = None) -> None:
    """Set a value. If ttl (seconds) is provided, it will expire after ttl."""
    expires_at = (_now() + float(ttl)) if ttl else None
    with _LOCK:
        _STORE[str(key)] = (value, expires_at)
        try:
            CACHE_SETS.inc()
        except Exception:
            pass
        _update_size_gauge()

def cache_get(key: str, default: Any = None) -> Any:
    """Get a value or default if missing/expired. Updates hit/miss metrics and hit-rate."""
    global _LOOKUPS_HITS, _LOOKUPS_MISSES
    k = str(key)
    with _LOCK:
        item = _STORE.get(k)
        if item is None:
            _LOOKUPS_MISSES += 1
            try:
                CACHE_MISSES.inc()
            except Exception:
                pass
            _update_hit_rate_gauge()
            return default

        value, expires_at = item
        if _expired(expires_at):
            _STORE.pop(k, None)
            _LOOKUPS_MISSES += 1
            try:
                CACHE_MISSES.inc()
            except Exception:
                pass
            _update_size_gauge()
            _update_hit_rate_gauge()
            return default

        _LOOKUPS_HITS += 1
        try:
            CACHE_HITS.inc()
        except Exception:
            pass
        _update_hit_rate_gauge()
        return value

def cache_invalidate(*keys: str, prefix: Optional[str] = None) -> int:
    """
    Invalidate cache entries.
      - cache_invalidate("k1", "k2") removes specific keys.
      - cache_invalidate(prefix="user:") removes keys starting with that prefix.
      - cache_invalidate() removes all keys.
    Returns the number of removed entries.
    """
    removed = 0
    with _LOCK:
        for k in keys or ():
            if _STORE.pop(str(k), None) is not None:
                removed += 1

        if prefix is not None:
            p = str(prefix)
            for k in list(_STORE.keys()):
                if k.startswith(p):
                    _STORE.pop(k, None)
                    removed += 1

        if not keys and prefix is None:
            removed = len(_STORE)
            _STORE.clear()

        if removed:
            try:
                CACHE_INVALIDATIONS.inc(removed)  # count entries invalidated
            except Exception:
                pass
        _update_size_gauge()

    return removed
def init_cache(app=None, **config):
    \"\"\"Compatibility initializer for the cache layer.

    Tests may call this to set up/clear cache. We keep our in-module
    cache implementation and just clear it, then update metrics.
    If a Flask app is provided, we ignore it (unless you later wire in
    Flask-Caching here).
    Returns True to signal initialization succeeded.
    \"\"\"
    with _LOCK:
        _STORE.clear()
    _update_size_gauge()
    return True
