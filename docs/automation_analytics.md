# Automation & Analytics

The automation layer uses Celery to schedule background tasks:

- **Approval reminders** – `send_approval_reminders` notifies sales representatives about pending orders every four hours.
- **Sales forecasting** – `forecast_sales` computes a simple trend-based projection on the first day of each month.
- **Compliance reporting** – `generate_compliance_report` emits weekly CSV listings of orders missing a status.

Use the web-based **Report Builder** at `/analytics/reports` to generate on-demand tables for orders and tenders. Results are rendered in a responsive Bootstrap table for quick export.
