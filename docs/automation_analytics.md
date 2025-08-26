# Automation & Analytics

The automation layer uses Celery to schedule background tasks:

- **Approval reminders** – `send_approval_reminders` notifies sales representatives about pending orders every four hours.
- **Sales forecasting** – `forecast_sales` computes a simple trend-based projection on the first day of each month.
- **Compliance reporting** – `generate_compliance_report` emits weekly CSV listings of orders missing a status.
- **Data hygiene** – `deduplicate_customers` removes duplicate CRM records nightly to keep master data clean.

Use the web-based **Report Builder** at `/reports/builder` to generate on-demand tables for orders and tenders. Results are rendered in a responsive Bootstrap table for quick export.

Monitor worker health with `python scripts/monitor_queue.py`, which prints the current Celery queue backlog. Sudden growth indicates stuck tasks.
