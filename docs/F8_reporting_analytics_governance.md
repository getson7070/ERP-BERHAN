# F8 — Reporting & Analytics Governance (Trusted Numbers)

## Objective
Make reports consistent, explainable, permission-aware, and reproducible for dashboards, APIs, and bots without conflicting with existing reporting work.

## Semantic Layer & Views
- Create versioned reporting views/models: `vw_sales_summary`, `vw_inventory_status`, `vw_client_activity`, `vw_employee_performance_kpis`, `vw_tender_pipeline` using canonical sources (ledger + reconciled movements).
- Prohibit ad-hoc "JOIN salads" in routes/templates; reports consume only these views to align logic across UI, exports, and bots.

## Report Definition Registry
- `ReportDefinition`: `code`, `name`, `description`, `data_source/sql_view`, `parameters_schema`, `access_min_role|required_permissions`, `version`, `is_active`.
- `/api/reports/run` resolves registry entry, validates params, enforces RBAC, and routes to the query builder.
- Deprecation model: publish new versions, allow dual-run during migration, retire old versions explicitly.

## Role-Based Access & Row Security
- Map report codes to roles/perms (finance vs inventory vs sales); enforce through a centralized gate to avoid leakage across tenants/orgs.
- Apply row filters where needed (e.g., sales reps see only owned clients); bots use scoped service accounts limited to whitelisted report codes.

## Deterministic Exports & Snapshots
- For formal outputs (tenders, bank packs), persist snapshots: report code + version, parameters, checksum/payload, actor, reason, timestamp.
- Enable reproduction of historical numbers even after logic changes; store in append-only table with audit logging.

## Performance & Observability
- Define runtime SLO per heavy report (e.g., ≤20s for 12 months); log each run in `report_run_log` with timing, status, actor, org.
- Flag SLO breaches on the integrity dashboard; consider materialized views or pre-aggregation for offenders.
- Emit Prometheus metrics (report counts, failures, latency) and Sentry traces for long-running queries.

## Governance & Anti-Shadow Analytics
- Involve domain owners to sign off metric definitions; publish definitions alongside views to discourage ungoverned Excel/CSV pipelines.
- Require approvals for new “board-level” reports and codify ownership; block unregistered ad-hoc SQL in production.

## Open Questions
- Which 3–5 board-critical reports move first into the semantic layer + snapshot model?
- How are conflicts between system numbers and human records resolved and evidenced?
- What friction level is acceptable during cleanup (alerts/blocks) versus gradual rollout?
