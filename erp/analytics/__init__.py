"""
Analytics public API.

Exposes forecasters, detectors, and tasks for use in app/tests.
"""

from dataclasses import dataclass
from typing import List, Sequence

@dataclass
class DemandForecaster:
    def forecast(self, history: Sequence[float]) -> float:
        if not history:
            return 0.0
        return sum(history) / len(history)


class InventoryAnomalyDetector:
    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def detect(self, values: Sequence[float]) -> List[int]:
        n = len(values)
        if n == 0:
            return []

        mean = sum(values) / n
        var = sum((v - mean) ** 2 for v in values) / n
        std = var ** 0.5

        if std == 0:
            return []

        indices = [i for i, v in enumerate(values) if abs(v - mean) > self.threshold * std]
        return indices


class RetrainAndPredictTask:
    def run(self, history: Sequence[float], inventory_levels: Sequence[float]) -> dict:
        forecaster = DemandForecaster()
        forecast = forecaster.forecast(history)

        detector = InventoryAnomalyDetector()
        anomalies = detector.detect(inventory_levels)

        return {"forecast": forecast, "anomalies": anomalies}


retrain_and_predict = RetrainAndPredictTask()

def materialized_view_state() -> dict:
    return {"status": "ok", "views": []}

__all__ = [
    "DemandForecaster",
    "InventoryAnomalyDetector",
    "retrain_and_predict",
    "materialized_view_state",
]