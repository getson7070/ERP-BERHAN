"""
Analytics public API.

Exposes simple forecasting and anomaly detection primitives plus a
small task-like helper used in tests.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class DemandForecaster:
    """Very small forecasting helper.

    - .fit(history) stores the series and returns self.
    - .predict_next() extrapolates a simple linear trend based on the
      last two points.
    - .forecast(history) returns the mean of the provided series.
    """

    history: List[float] = field(default_factory=list)

    def fit(self, history: Sequence[float]) -> "DemandForecaster":
        self.history = list(history)
        return self

    def predict_next(self) -> float:
        if not self.history:
            return 0.0
        if len(self.history) == 1:
            return float(self.history[0])
        last = float(self.history[-1])
        prev = float(self.history[-2])
        trend = last - prev
        return last + trend

    def forecast(self, history: Sequence[float]) -> float:
        if not history:
            return 0.0
        return float(sum(history) / len(history))


class InventoryAnomalyDetector:
    def __init__(self, threshold: float = 1.0):
        self.threshold = float(threshold)

    def detect(self, values: Sequence[float]) -> List[int]:
        n = len(values)
        if n == 0:
            return []

        mean = sum(values) / n
        var = sum((v - mean) ** 2 for v in values) / n
        std = var ** 0.5

        if std == 0:
            return []

        return [
            i
            for i, v in enumerate(values)
            if abs(v - mean) > self.threshold * std
        ]


class RetrainAndPredictTask:
    """Shim object with .run(...) used by tests like a Celery task."""

    def run(self, history: Sequence[float], inventory_levels: Sequence[float]) -> dict:
        forecaster = DemandForecaster()
        forecast = forecaster.forecast(history)

        detector = InventoryAnomalyDetector()
        anomalies = detector.detect(inventory_levels)

        return {"forecast": forecast, "anomalies": anomalies}


retrain_and_predict = RetrainAndPredictTask()


def materialized_view_state() -> dict:
    """Placeholder helper for future analytics materialized views."""
    return {"status": "ok", "views": []}


__all__ = [
    "DemandForecaster",
    "InventoryAnomalyDetector",
    "retrain_and_predict",
    "materialized_view_state",
]
