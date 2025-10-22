from __future__ import annotations
from typing import Iterable, List
import statistics as stats
from datetime import datetime, timezone

__all__ = ["DemandForecaster", "InventoryAnomalyDetector", "retrain_and_predict", "materialized_view_state"]

_MV_STATE = {"last_refreshed": None, "values": []}

class DemandForecaster:
    def __init__(self) -> None:
        self._series: List[float] = []
        self._step: float = 0.0

    def fit(self, series: Iterable[float]) -> "DemandForecaster":
        xs = list(series)
        self._series = xs
        if len(xs) >= 2:
            diffs = [b - a for a, b in zip(xs, xs[1:])]
            self._step = sum(diffs) / len(diffs)
        else:
            self._step = 0.0
        return self

    def predict_next(self) -> float:
        last = self._series[-1] if self._series else 0.0
        return last + self._step

class InventoryAnomalyDetector:
    def __init__(self, threshold: float = 3.0) -> None:
        self.threshold = float(threshold)

    def detect(self, data: Iterable[float]) -> List[float]:
        xs = list(data)
        if not xs:
            return []
        mu = stats.mean(xs)
        sigma = stats.pstdev(xs) or 1e-12
        return [x for x in xs if abs((x - mu) / sigma) >= self.threshold]

def _retrain_and_predict_core(history: Iterable[float], inventory_series: Iterable[float], anomaly_threshold: float = 2.0):
    forecaster = DemandForecaster().fit(history)
    forecast = forecaster.predict_next()
    anomalies = InventoryAnomalyDetector(threshold=anomaly_threshold).detect(inventory_series)
    _MV_STATE["last_refreshed"] = datetime.now(timezone.utc)
    _MV_STATE["values"] = [forecast]
    return {"forecast": forecast, "anomalies": anomalies}

class _Task:
    def __init__(self, func):
        self.name = "erp.analytics.retrain_and_predict"
        self._func = func
    def run(self, *args, **kwargs):
        return self._func(*args, **kwargs)

retrain_and_predict = _Task(_retrain_and_predict_core)

def materialized_view_state():
    return _MV_STATE.copy()