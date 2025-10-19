from analytics.ml import DemandForecaster, InventoryAnomalyDetector
from erp.analytics import retrain_and_predict


def test_demand_forecaster_predicts_next():
    forecaster = DemandForecaster().fit([1, 2, 3, 4])
    next_val = forecaster.predict_next()
    assert next_val > 4


def test_anomaly_detector_flags_outliers():
    detector = InventoryAnomalyDetector(threshold=1.0)
    anomalies = detector.detect([10, 10, 100])
    assert anomalies == [2]


def test_celery_task_returns_forecast_and_anomalies():
    result = retrain_and_predict.run([1, 2, 3], [1, 2, 30])
    assert "forecast" in result and "anomalies" in result


