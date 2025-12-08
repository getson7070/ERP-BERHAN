# Layer 7 Audit – Reporting, Analytics & Performance Evaluation

## Scope
Evaluate analytics facts, scorecards, reporting APIs, and bot/query surfaces against requirements for robust reporting, employee performance evaluation, and recommendations.

## Current Capabilities
- **Scorecard computation engine**: `compute_scorecard` aggregates KPI facts by subject (employee/client/item/warehouse), applies weighted scoring, and returns breakdowns for dashboards or evaluations.【F:erp/services/performance_engine.py†L1-L98】
- **Bot analytics surface**: Telegram bot handlers expose `analytics_query` to list top performance evaluations per cycle, enabling lightweight reporting via chat alongside approvals and inventory lookups.【F:erp/bots/handlers.py†L1-L58】
- **Analytics ingestion tasks**: Background task scaffold for nightly rollups into `AnalyticsFact` exists (placeholder), indicating pipeline intent for metrics consolidation.【F:erp/tasks/analytics_rollup.py†L1-L53】

## Gaps & Risks vs. Requirements
- **Coverage of business domains**: Current analytics focus on scorecards; missing comprehensive reports for sales, finance, maintenance, procurement, marketing, HR, and CRM needed for the requested dashboards and recommendations.
- **Predictive/AI recommendations**: No implemented recommendation or anomaly detection; predictive tasks are placeholders without models or outputs for purchase/sales/client recommendations.
- **Drilldowns & permissions**: Reporting endpoints are not clearly RBAC-scoped by role (client/employee/supervisor/admin) nor aligned to tenant org; need per-role dashboard tailoring.
- **Data quality & freshness**: No SLAs or validation for analytics fact freshness; rollup tasks lack monitoring, retries, or observability.
- **UX modernization**: Reporting UI/exports are not referenced; need responsive dashboards, filters, and accessible visualizations consistent with industry standards.

## Recommendations
1. **Expand metrics catalog** across sales, finance, maintenance, procurement, marketing, HR with governed KPI definitions and per-role visibility.
2. **Implement predictive analytics** (churn, demand, delay risk) and recommendation surfaces; integrate into dashboards and bot responses with auditability.
3. **Harden pipeline** with scheduled Celery tasks, backfill/retry, data validation, and freshness alerts; log lineage for compliance.
4. **RBAC-aware reporting** ensuring clients see only their org data; supervisors/admins get approvals/commission views; auditors get read-only exports.
5. **Modern reporting UX**: responsive web dashboards, CSV/Excel export, email/PDF scheduling, accessible charts, and drilldowns with consistent theming.
