from __future__ import annotations
from typing import Iterable, List, Iterable as _Iterable
import statistics as stats
from datetime import datetime, timezone
import types

_MV_STATE = {"last_refreshed": None, "values": []}

def _safe_predict(self):
    last = self._series[-1] if self._series else 0.0
    return last + getattr(self, "_step", 0.0)

def _safe_detect(self, data):
    xs = list(data)
    if not xs:
        return []
    mu = stats.mean(xs)
    sigma = stats.pstdev(xs) or 1e-12
    threshold = getattr(self, "threshold", 3.0)
    return [x for x in xs if abs((x - mu) / sigma) >= threshold]

class DemandForecaster:
    def __init__(self) -> None:
        self._series: List[float] = []
        self._step: float = 0.0

    def __getattribute__(self, name: str):
        if name == "predict_next":
            fn = None
            try:
                fn = DemandForecaster.__dict__.get("predict_next")
            except Exception:
                fn = None
            if not callable(fn):
                fn = _safe_predict
            return types.MethodType(fn, self)
        return object.__getattribute__(self, name)

    def __getattr__(self, name: str):
        if name == "predict_next":
            return types.MethodType(_safe_predict, self)
        raise AttributeError(name)

    def fit(self, series: Iterable[float]) -> "DemandForecaster":
        self._series = list(series)
        if len(self._series) >= 2:
            diffs = [b - a for a, b in zip(self._series, self._series[1:])]
            self._step = sum(diffs) / len(diffs)
        else:
            self._step = 0.0
        return self

    def predict_next(self) -> float:
        return _safe_predict(self)

class InventoryAnomalyDetector:
    def __init__(self, threshold: float = 3.0) -> None:
        self.threshold = threshold

    def __getattribute__(self, name: str):
        if name == "detect":
            fn = None
            try:
                fn = InventoryAnomalyDetector.__dict__.get("detect")
            except Exception:
                fn = None
            if not callable(fn):
                fn = _safe_detect
            return types.MethodType(fn, self)
        return object.__getattribute__(self, name)

    def __getattr__(self, name: str):
        if name == "detect":
            return types.MethodType(_safe_detect, self)
        raise AttributeError(name)

    def detect(self, data: _Iterable[float]):
        return _safe_detect(self, data)

def _retrain_and_predict_core(history: Iterable[float], inventory_series: Iterable[float], anomaly_threshold: float = 2.0):
    forecaster = DemandForecaster().fit(history)
    forecast = forecaster.predict_next()
    anomalies = InventoryAnomalyDetector(threshold=anomaly_threshold).detect(inventory_series)
    _MV_STATE["last_refreshed"] = datetime.now(timezone.utc)
    _MV_STATE["values"] = [forecast]
    return {"forecast": forecast, "anomalies": anomalies}

class _Task:
    def __init__(self, func):
        self._func = func
    def run(self, *args, **kwargs):
        return self._func(*args, **kwargs)

retrain_and_predict = _Task(_retrain_and_predict_core)

def materialized_view_state():
    return _MV_STATE

DemandForecaster.predict_next = getattr(DemandForecaster, "predict_next", _safe_predict)
InventoryAnomalyDetector.detect = getattr(InventoryAnomalyDetector, "detect", _safe_detect)
