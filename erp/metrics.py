class _Value:
    def __init__(self, v=0): self._v=v
    def get(self): return self._v
    def set(self, v): self._v=v

class _Counter:
    def __init__(self): self._value=_Value(0)
    def inc(self, n=1): self._value.set(self._value.get()+n); return self
    def labels(self, *_, **__): return self  # simple stub

class _Gauge:
    def __init__(self): self._value=_Value(0)
    def set(self, v): self._value.set(v); return self
    def labels(self, *_, **__): return self

GRAPHQL_REJECTS = _Counter()
RATE_LIMIT_REJECTIONS = _Counter()
QUEUE_LAG = _Gauge()
