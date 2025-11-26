# F3 — Reporting & Analytics Pipeline Addendum

This blueprint extends prior reporting upgrades with durable, auditable data pipelines while staying compatible with existing modules and RBAC.

## Objectives
- Provide a single, auditable reporting source that aligns with transactional data.
- Prevent drift through idempotent ETL and declarative report definitions.
- Enforce access control, lineage, and data quality for Inventory, Orders, and Finance insights.

## Reporting Data Model
- Establish fact tables: `fact_orders`, `fact_inventory_movements`, `fact_payments`, `fact_sales_activities`.
- Establish dimensions: `dim_date`, `dim_client`, `dim_product`, `dim_employee`, `dim_region`.
- All dashboards/exports draw from these facts/dimensions—no direct ad-hoc joins to transactional tables.

## ETL Jobs
- Schedule incremental, idempotent syncs (Celery beat/cron): orders, inventory, payments.
- Use high-watermarks per job run and idempotency keys (e.g., `orders:YYYY-MM-DD:HH`).
- Log each ETL run to `ETLJobLog`/`BotEvent` with success/failure and ranges processed.

## Declarative Report Definitions
- Define reports as configs (YAML/JSON) with report id, fact table, dimensions, measures, filters.
- Build a small interpreter to convert definitions into SQL/ORM queries for web dashboards, API exports, and scheduled bot/email sends.
- Maintain versioning so logic changes can coexist (e.g., v1 vs v2) during rollouts.

## Access Control and Auditing
- Map each report to required roles/permissions and optional row-level filters (e.g., reps see their accounts; region heads see their regions).
- Executor enforces RBAC and injects org-scoped filters; every run logs user, filters, export type, and timestamp.

## Scheduled Reports & Bot Integration
- Use the same declarative definitions for scheduled Telegram/email reports (daily inventory summaries, weekly sales, monthly aging/payments).
- Allow async generation for heavy reports; reuse background queues and job tracking.

## Data Quality & Testing
- Tests verify ETL idempotency and metric reconciliation (fact totals vs transactional sums).
- Sanity checks: null-critical fields, referential integrity between facts/dimensions, flag negative/implausible quantities.
- Avoid N+1 and performance regressions by reusing caching and queue patterns from earlier tasks.

## Security, UX, and Compliance Notes
- Respect data classification: limit sensitive fields in logs/exports; prefer IDs and minimal context.
- Provide clear UI messaging for report access denials and long-running jobs (progress/polling states).
- Keep migrations additive and indexed on `org_id`/time keys for multi-tenant performance.
