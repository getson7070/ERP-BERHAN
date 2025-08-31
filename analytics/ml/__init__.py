"""Predictive analytics models for ERP-BERHAN.

This module provides lightweight demand forecasting and inventory
anomaly detection utilities backed by scikit-learn. The models are
kept intentionally simple so they can run inside Celery workers and be
extended in production deployments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np
from sklearn.linear_model import LinearRegression


@dataclass
class DemandForecaster:
    """Linear regression based demand forecaster.

    A tiny wrapper around :class:`~sklearn.linear_model.LinearRegression`
    that predicts the next value in a time series.
    """

    model: LinearRegression | None = None
    _n_samples: int = 0

    def fit(self, history: Sequence[float]) -> "DemandForecaster":
        self._n_samples = len(history)
        x = np.arange(self._n_samples).reshape(-1, 1)
        y = np.array(history, dtype=float)
        self.model = LinearRegression().fit(x, y)
        return self

    def predict_next(self) -> float:
        if self.model is None:
            raise RuntimeError("Model has not been fitted")
        next_step = np.array([[self._n_samples]])
        return float(self.model.predict(next_step)[0])


@dataclass
class InventoryAnomalyDetector:
    """Statistical z-score anomaly detector."""

    threshold: float = 2.5

    def detect(self, values: Sequence[float]) -> List[int]:
        arr = np.array(values, dtype=float)
        if arr.size == 0:
            return []
        mean = arr.mean()
        std = arr.std() or 1.0
        z_scores = np.abs((arr - mean) / std)
        return [int(i) for i, z in enumerate(z_scores) if z > self.threshold]
