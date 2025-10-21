from __future__ import annotations
import statistics

class DemandForecaster:
    def __init__(self): self._series = []
    def fit(self, series): self._series = list(series); return self
    def predict_next(self):
        if len(self._series) < 2: return (self._series[-1] if self._series else 0)
        return self._series[-1] + (self._series[-1] - self._series[-2])

class InventoryAnomalyDetector:
    def __init__(self, threshold=2.0): self.threshold = threshold
    def detect(self, series):
        if not series: return []
        mu = statistics.mean(series)
        sd = statistics.pstdev(series) or 1.0
        return [x for x in series if abs(x - mu) > self.threshold * sd]

def kpi_staleness_seconds() -> float:
    # monkeypatched by tests; default harmless value
    return 0.0
