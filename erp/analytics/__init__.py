"""Analytics blueprint stubs and forecasting helpers."""
from __future__ import annotations

from statistics import fmean
from typing import Iterable, Sequence

from flask import Blueprint, jsonify

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@bp.get("/health")
def health():
    return jsonify(module="analytics", ok=True)


class DemandForecaster:
    """Lightweight forecasting stub to keep blueprints importable during scaffolding."""

    def __init__(self) -> None:
        self._history: list[float] = []

    def fit(self, history: Sequence[float] | Iterable[float]) -> "DemandForecaster":
        self._history = [float(v) for v in history]
        return self

    def predict_next(self) -> float:
        if not self._history:
            return 0.0
        return float(self._history[-1])


def retrain_and_predict(history: Sequence[float] | Iterable[float]) -> float:
    cleaned = [float(v) for v in history if v is not None]
    if not cleaned:
        return 0.0
    baseline = cleaned[-1]
    trend = fmean(cleaned[-3:]) if len(cleaned) >= 3 else baseline
    return DemandForecaster().fit(cleaned).predict_next() or trend


__all__ = ["bp", "DemandForecaster", "retrain_and_predict", "health"]
__all__ = ["bp", "DemandForecaster", "retrain_and_predict", "health"]
