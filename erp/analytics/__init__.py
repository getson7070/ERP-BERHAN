"""Celery tasks for predictive analytics."""

from __future__ import annotations

from celery import shared_task
from prometheus_client import Gauge

from analytics.ml import DemandForecaster, InventoryAnomalyDetector

forecast_gauge = Gauge("demand_forecast", "Predicted next demand units")


@shared_task(name="analytics.retrain_and_predict")
def retrain_and_predict(
    sales_history: list[float], inventory_levels: list[float]
) -> dict:
    """Retrain models and return forecast/anomaly data.

    The task is intentionally simple; in production the trained models
    would be persisted and metrics pushed to Prometheus.
    """
    forecaster = DemandForecaster().fit(sales_history)
    forecast = forecaster.predict_next()
    forecast_gauge.set(forecast)

    detector = InventoryAnomalyDetector()
    anomalies = detector.detect(inventory_levels)

    return {"forecast": forecast, "anomalies": anomalies}
