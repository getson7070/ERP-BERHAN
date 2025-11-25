# F3 – Reporting & Analytics Fabric

This document defines the implementation blueprint for making ERP-BERHAN reports trustworthy, explainable, and governed while remaining compatible with existing modules and prior upgrades (including the 21-task upgrade and F1/F2).

## Objectives
- Centralize reporting logic so every report uses the same vetted query layer.
- Provide versioned, auditable report definitions to avoid silent logic drift.
- Enforce RBAC consistently across reporting surfaces and prevent ad-hoc SQL in views.
- Keep performance and observability in mind (read replicas/materialized views as needed) without breaking current flows.

## Architecture
```
erp/
  reporting/
    __init__.py
    models.py        # Registry + optional materialized summaries
    queries.py       # Canonical query builders (ORM/SQL)
    services.py      # Report API surface with RBAC + validation
    views.py         # HTTP/JSON endpoints consuming services
```

### Core principles
- **Single entrypoint**: complex report SQL lives only in `reporting.queries` and is exposed via `reporting.services`. Views/templates call the service, never raw SQL.
- **Versioned definitions**: track report identities and versions in a registry table so logic changes are explicit and selectable during migrations.
- **RBAC-first**: every report checks role/permission via a shared helper before executing queries.
- **Additive rollout**: new reporting layer coexists with current routes; consumers are migrated incrementally.

## Initial report set
Start with four report families that align with current risk hotspots:

1. **Inventory**
   - Stock on hand by item/warehouse (as-of capable).
   - Items with frequent discrepancies (F1) or oversell attempts (F2).

2. **Orders & Fulfilment**
   - Open orders by age/status.
   - Fill rate, lead time, cancellation reasons.

3. **Sales/Client**
   - Revenue by client/region/product line.
   - Quote → order → paid funnel conversion.

4. **Operational/Bot**
   - Bot commands per user/module.
   - Failed bot jobs and MTTR per incident type.

Each report is a function in `reporting.queries`, e.g.:
```python
def q_inventory_snapshot(org_id, as_of=None):
    """Base query for stock-on-hand reports (scoped by org)."""
    ...
```
`services.py` wraps these with pagination, RBAC enforcement, parameter validation, and response shaping.

## Report registry model (additive)
Add a lightweight registry in `erp/reporting/models.py`:
- `id` (int, PK)
- `org_id` (nullable; NULL = global)
- `code` (string, indexed; e.g., `inventory_snapshot`)
- `version` (string, default `v1`)
- `description` (string)
- `is_active` (bool, default `True`)
- `created_at` (tz-aware timestamp, default `now()`)

This tracks which version is in use; SQL/ORM logic remains in code. When business rules change (e.g., valuation method), add `version='v2'` and allow dual-run during migration before retiring `v1`.

## RBAC alignment
Use existing role upgrades (Task 17) and define per-report requirements in one place, e.g. `reporting.services.ensure_can_view_report(user, code)`. Suggested mapping:
- `ROLE_EXEC`: all financial + HR + inventory reports.
- `ROLE_FINANCE`: finance + inventory valuation.
- `ROLE_INVENTORY`: quantities/operational metrics (no sensitive financials).
- `ROLE_SALES`: scoped to own sales/clients.

## Testing
Create `tests/reporting/test_fabric.py` to ensure:
- Every registered `report_code` has a matching query function and at least one test.
- RBAC enforcement: insufficient role → 403/denied; sufficient role → success.
- Version changes are explicit: a computation change increments `version`, and tests assert the correct version is served.

## Performance and data freshness
- Prefer read replicas for heavy reports when available.
- Materialized views are optional; if used, document refresh cadence and ensure transactional/consistent refresh where needed.
- Monitor query latency; add indexes based on real workloads.

## Observability
- Log report executions with user/org, report_code, version, duration, and parameters (excluding sensitive filters).
- Metrics: counters for executions by result (success/fail), gauge for stale materialized views, and alerts for unusual error spikes.

## Rollout
1. **Dark launch**: build reporting layer and registry; mirror existing reports without changing UI behaviour.
2. **Incremental migration**: move high-risk reports (inventory availability, oversell attempts, discrepancy trends) to the new layer first.
3. **Deprecation**: retire ad-hoc queries/views once replaced; enforce a lint/test that complex queries must live in `reporting.queries`.
