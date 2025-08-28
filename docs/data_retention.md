# Data Retention and Lineage

This policy defines how long data is kept and documents column‑level lineage.

## Retention Matrix
| Table | Retention Period | Notes |
|-------|-----------------|-------|
| `inventory_items` | 7 years | Regulatory stock history |
| `invoices` | 10 years | Financial compliance |
| `audit_logs` | 10 years | Tamper‑evident chain |

## Lineage Tracking
The `data_lineage` table records the origin of columns used in analytics.
Populate the table whenever new ETL or reports are added.

```sql
INSERT INTO data_lineage(table_name, column_name, source)
VALUES ('kpi_sales', 'total', 'invoices.total');
```

## PII Handling

Personally identifiable fields are classified and masked before export:

- `users.email` is SHA256-hashed when aggregated into analytics tables.
- `clients.phone` is stored encrypted and truncated to the last four digits in reports.
- Exports to external warehouses (TimescaleDB/ClickHouse) strip or anonymize PII in accordance with Ethiopian data protection law and are subject to the same retention windows.
