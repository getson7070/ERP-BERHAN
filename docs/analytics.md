# Analytics & Automation

## Celery Workflows
- `generate_report`: builds daily CSV summaries of orders and maintenance.
- `expire_tenders`: closes overdue tenders every night.
- `refresh_kpis`: refreshes the `kpi_sales` materialized view every five minutes.
- `check_kpi_staleness`: warns if `kpi_sales` is stale for more than ten minutes; staleness is tracked via the `kpi_sales_mv_age_seconds` gauge in `/metrics`.
- `export_kpis_to_olap`: nightly export of KPIs to a TimescaleDB or ClickHouse warehouse for long-range analytics.
- `send_approval_reminders`: logs and notifies managers of pending order approvals each morning.
- `forecast_sales`: predicts next month's sales from recent KPIs.
- `generate_compliance_report`: exports a list of unapproved orders for auditing.
- `build_custom_report`: creates ad-hoc CSV exports for orders or maintenance.
- `collect_feedback`: stores optional usage feedback from `/feedback/` and
  front-end telemetry for future analysis.

## Report Builder
Navigate to `/analytics/report-builder` to assemble ad-hoc reports using a drag-and-drop interface. Outputs can be exported to PDF or Excel. Ensure `CELERY_BROKER_URL`
and `CELERY_RESULT_BACKEND` are configured and a worker is running:

```bash
celery -A erp.routes.analytics.celery worker --beat
```

## Forecasting
The dashboard displays a projected next-month sales figure computed as the average of the last three months of `kpi_sales` data.

## Compliance Reports
Selecting **Compliance** in the report builder schedules a generator that scans for orders without approvals and writes a CSV report for audit review.
