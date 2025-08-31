# Predictive Analytics

BERHAN now ships with a lightweight predictive analytics service. Demand
forecasts and inventory anomaly detection are executed via Celery tasks
backed by scikit-learn models. Forecast metrics are exposed through
Prometheus gauges for dashboard visualisation.

## Workflow
1. Sales and inventory history are passed to the
   `analytics.retrain_and_predict` task.
2. The task retrains models on the fly and emits a demand forecast and
   anomaly indices.
3. Prometheus collects the forecast gauge, allowing dashboards to render
   near real-time insights.
