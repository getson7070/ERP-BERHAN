# Reporting & Analytics

## Unified Analytics Layer
All KPIs are normalized into:
- `AnalyticsMetric` (registry)
- `AnalyticsFact` (daily facts table)

This allows cross-module dashboards and BI tools to read a single schema.

## Dashboards
- Role dashboards via `AnalyticsDashboard.for_role`
- Widgets via `AnalyticsWidget`
- Widgets reference `metric_key` from the registry

Endpoints:
- `GET /api/analytics/metrics`
- `GET /api/analytics/fact`
- `GET /api/analytics/dashboards`
- `POST /api/analytics/dashboards`

## BI Integration
Stable views for Superset/Metabase:
- `bi_daily_metrics`
- `bi_metrics_registry`

## Predictive Analytics
Celery tasks write forecasts into:
- `metric_key + ".forecast"`

## Data Lineage & Privacy
Lineage stored in `analytics_lineage`.
Privacy enforced by `privacy_class`:
- public, internal, sensitive, pii
Sensitive/PII metrics require admin.
