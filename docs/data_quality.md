# Master Data Hygiene

Nightly tasks deduplicate CRM records and check for timestamp conflicts.

- `deduplicate(table, fields)` removes duplicate rows using SQL.
- `detect_conflict(existing, incoming)` flags stale updates so clients can handle sync collisions.

See `erp/data_quality.py` and Celery task `deduplicate_customers` for usage.
