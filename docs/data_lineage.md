# Data Refresh and Lineage

- **Incremental Materialized Views**: Heavy reports use PostgreSQL incremental refresh to avoid full rebuilds.
- **MV Age Alerts**: A scheduled job checks `pgmatviews` and alerts when `last_refresh` exceeds five minutes.
- **Lineage Tracking**: Each ETL step logs source tables and transforms in `data_lineage` tables for auditability.
- **Analytics Freshness**: Standard refresh cadence is five minutes with automatic catch-up after downtime.
