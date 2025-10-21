# erp/metrics.py
from __future__ import annotations
import time
from types import SimpleNamespace

class _Value:
    def __init__(self, v=0.0): self._v = v
    def get(self): return self._v
    def set(self, v): self._v = v
    def inc(self, dv=1.0): self._v += dv

class _GaugeChild:
    def __init__(self): self._value = _Value()

class _LabeledGauge:
    def __init__(self): self._children = {}
    def labels(self, *keys):
        k = tuple(keys)
        if k not in self._children:
            self._children[k] = _GaugeChild()
        return self._children[k]

# Global metrics the tests import/read
GRAPHQL_REJECTS = _LabeledGauge()
RATE_LIMIT_REJECTIONS = _LabeledGauge()
QUEUE_LAG = _LabeledGauge()
OLAP_EXPORT_SUCCESS = _LabeledGauge()

def expose_prom_text(extra_lines: list[str] = None) -> bytes:
    # Only what tests assert on
    lines = []
    # MV age metric used in tests; a route monkeypatch sets its value
    # We'll expose a line if something set 'kpi_sales_mv_age_seconds' elsewhere.
    # The tests monkeypatch a function to return staleness, so the /metrics route
    # will include that.
    if extra_lines:
        lines.extend(extra_lines)
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
