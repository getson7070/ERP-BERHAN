from __future__ import annotations
from statistics import mean, pstdev
from typing import Iterable, List, Dict, Any

class DemandForecaster:
    def __init__(self) -> None:
        self.series: List[float] = []

    def fit(self, series: Iterable[float]):
        self.series = list(series or [])
        return self

    def predict_next(self) -> float:
        n = len(self.series)
        if n == 0:
            return 0
        if n == 1:
            return self.series[-1]
        diffs = [b - a for a, b in zip(self.series[:-1], self.series[1:])]
        return self.series[-1] + round(mean(diffs))

class InventoryAnomalyDetector:
    def __init__(self, threshold: float = 2.0) -> None:
        self.threshold = float(threshold)

    def detect(self, xs: Iterable[float]) -> List[int]:
        xs = list(xs or [])
        if not xs:
            return []
        mu = mean(xs)
        sigma = pstdev(xs)
        if not sigma:
            return []
        limit = mu + self.threshold * sigma
        return [i for i, v in enumerate(xs) if v > limit]

def _predict(train_series: Iterable[float], observed_series: Iterable[float]) -> Dict[str, Any]:
    f = DemandForecaster().fit(train_series)
    nxt = f.predict_next()
    anomalies = InventoryAnomalyDetector(threshold=1.5).detect(observed_series)
    return {"forecast": nxt, "anomalies": anomalies}

class _Task:
    def run(self, train_series: Iterable[float], observed_series: Iterable[float]) -> Dict[str, Any]:
        return _predict(train_series, observed_series)

def retrain_and_predict_func(train_series: Iterable[float], observed_series: Iterable[float]) -> Dict[str, Any]:
    return _predict(train_series, observed_series)

retrain_and_predict = _Task()