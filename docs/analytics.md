# Automation & Analytics

The analytics blueprint exposes reporting and forecasting utilities backed by Celery.

## Celery Tasks
- `send_order_reminders` – logs reminders for all pending orders every morning.
- `build_report` – generates CSV summaries of field reports for a given date range.
- `forecast_sales` – predicts next month's sales using simple trend analysis.
- `generate_compliance_report` – aggregates orders per customer for regulatory audits.

## Web Interfaces
- `/analytics/report-builder` – management users create custom CSV exports.
- `/analytics/forecast` – displays the upcoming month's projected sales.

Ensure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are configured and a worker is running:

```bash
celery -A erp.routes.analytics.celery worker --beat
```
