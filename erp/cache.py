from typing import Any
try:
    from prometheus_client import Counter, Gauge  # type: ignore
except Exception:
    class _M:
        def __init__(self, *_, **__): self.value = 0
        def inc(self, n: float = 1): self.value += n
        def dec(self, n: float = 1): self.value -= n
        def set(self, v: float): self.value = v
        def labels(self, *_, **__): return self
    def Counter(*args, **kwargs): return _M()
    def Gauge(*args, **kwargs): return _M()

_CACHE: dict[str, Any] = {}

def init_cache(): return True
def cache_set(key: str, value: Any, ttl: int | None = None) -> bool:
    _CACHE[key] = value; return True
def cache_get(key: str) -> Any | None:
    return _CACHE.get(key)
def cache_invalidate(key: str) -> bool:
    _CACHE.pop(key, None); return True
