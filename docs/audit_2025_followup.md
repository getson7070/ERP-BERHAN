# October 2025 Follow-up Audit

This assessment revisits the September 2025 audit focus areas and scores the current `main` branch as of October 2025. Ratings reflect implementation maturity, security posture, and operational readiness.

## Scorecard

| Domain | Sept 2025 Score | Current Score | Trend | Summary |
| --- | --- | --- | --- | --- |
| Security | 8.7 | 7.9 | ▼ | CI gates remain comprehensive but runtime auth is fragmented and permission checks are undefined in live routes. |
| User-friendliness | 7.8 | 6.6 | ▼ | The design system advanced, yet HR workflows render missing templates so core pages fail to load. |
| Database | 7.6 | 6.8 | ▼ | Backups and index tooling are strong, but critical modules still issue raw SQL and lack ORM models. |
| Code quality | 8.1 | 6.9 | ▼ | Multiple blueprints import helpers and models that do not exist, causing import errors before the app can boot. |
| Web access | 8.2 | 7.2 | ▼ | Base routing is intact, however unfinished report builder views are exposed without feature flags or templates. |
| Integration | 8.5 | 7.9 | ▼ | Connectors and SDK docs persist, but operator guidance for Celery/Redis remains undocumented. |
| Inter-function communication | 8.2 | 6.5 | ▼ | HR forms still cannot persist because the referenced models and templates are missing from the codebase. |
| Performance | 8.3 | 8.0 | ▬ | Index audits and backup telemetry continue to ship, yet missing ORM layers prevent slow-query instrumentation from maturing. |

## Domain Findings

### Security (7.9)
* **What improved:** The CI workflow still enforces extensive gates (lint, mypy, security scanners, Pa11y, Trivy, ZAP, SBOM, signed artifacts), preserving the strong preventative posture highlighted last cycle.【F:.github/workflows/ci.yml†L1-L105】
* **What regressed:** Runtime permission checks are broken because `orders` and `tenders` blueprints import `has_permission` from `erp.utils`, yet that helper is not defined anywhere in the module, so the import raises and the decorators never execute.【F:erp/routes/orders.py†L16-L190】【F:erp/utils.py†L310-L323】 Mixing Flask-Login sessions in `auth` with JWT-only decorators elsewhere deepens the split authentication stack the prior audit flagged for consolidation.【F:erp/routes/auth.py†L1-L54】

### User-friendliness (6.6)
* **What improved:** The base stylesheet now ships a modern dark-mode token set, responsive spacing, and refined focus states that align with current design system guidance.【F:erp/static/css/base.css†L1-L160】
* **What regressed:** The HR recruitment and performance routes render templates under `hr/…`, but no such templates exist in the repository, so the pages 404 instead of presenting the evolving UI called out last quarter.【F:erp/routes/hr_workflows.py†L19-L68】【637001†L1-L2】

### Database (6.8)
* **What improved:** Backup automation continues to emit checksum manifests and JSONL telemetry, sustaining the audit trail recommended previously.【F:scripts/pg_backup.sh†L2-L60】 The index audit script still fails builds when sequential scans lack indexes, providing actionable performance diagnostics.【F:scripts/index_audit.py†L1-L66】
* **What regressed:** Orders and tender flows still rely on manual SQL text instead of SQLAlchemy services, contradicting the migration guidance and making tenant scoping harder to guarantee.【F:erp/routes/orders.py†L45-L190】【F:erp/routes/tenders.py†L1-L120】 The HR models referenced by routes (`Recruitment`, `PerformanceReview`) are absent from `erp/models.py`, so persistence cannot work.【F:erp/routes/hr_workflows.py†L29-L65】【F:erp/models.py†L1-L27】

### Code Quality (6.9)
* **What improved:** Accessibility automation (Pa11y CLI) and lint/test coverage remain wired through CI and scripts, keeping standards visible to developers.【F:scripts/run_pa11y.sh†L1-L4】【F:.github/workflows/ci.yml†L60-L104】
* **What regressed:** Several blueprints depend on undefined symbols (`has_permission`, `Recruitment`, `UserDashboard`, `report_builder.html`), so imports fail and modules cannot load, signaling gaps in helper consistency noted in the last audit.【F:erp/routes/orders.py†L16-L190】【F:erp/routes/hr_workflows.py†L11-L68】【F:erp/routes/dashboard_customize.py†L1-L24】【c655b7†L11-L44】【bc8078†L1-L2】

### Web Access (7.2)
* **What improved:** The API blueprint keeps lightweight health routes protected by Flask-Limiter, matching the “blueprint routing solid” comment from September.【F:erp/routes/api.py†L1-L10】
* **What regressed:** The report builder UI is publicly routed without a guard or template, even though documentation still treats it as feature-flagged work-in-progress, leaving unfinished endpoints exposed to users.【c655b7†L11-L44】【0358e2†L10-L12】

### Integration (7.9)
* **What improved:** Integration documentation continues to enumerate REST, GraphQL, webhook endpoints, SDK helpers, and connectors, ensuring consumers know where to plug in.【F:docs/integrations.md†L1-L33】
* **What regressed:** Operator-facing instructions for Celery/Redis (broker URLs, worker scaling, failure recovery) are still absent—automation docs only list task names—so platform teams lack the runbooks the previous audit requested.【0358e2†L3-L12】

### Inter-function Communication (6.5)
* HR forms post to nonexistent ORM models, so nothing links the UI to the persistence layer, leaving analytics and downstream tasks without the data the audit expected to be wired up by now.【F:erp/routes/hr_workflows.py†L29-L65】【F:erp/models.py†L1-L27】

### Performance (8.0)
* Scripts that gather index health and backup telemetry continue to run, supporting slow-query investigations and RPO/RTO evidence.【F:scripts/index_audit.py†L1-L66】【F:scripts/pg_backup.sh†L2-L60】 However, without ORM-backed entities for HR and reporting modules, it remains difficult to capture slow-query metrics or apply automated optimizations across the full stack.【F:erp/routes/orders.py†L45-L190】【F:erp/routes/hr_workflows.py†L29-L65】

## Recommendations
1. Restore permission middleware (`has_permission`) and unify JWT vs Flask-Login flows before shipping to production; otherwise the security score will continue to fall.【F:erp/routes/orders.py†L16-L190】【F:erp/routes/auth.py†L1-L54】
2. Commit the missing HR models and templates, then bind them through SQLAlchemy services to satisfy both UX and database remediation goals.【F:erp/routes/hr_workflows.py†L19-L68】【F:erp/models.py†L1-L27】
3. Replace raw SQL in orders/tenders with tenant-scoped ORM queries so role checks, auditing, and slow-query logging apply consistently.【F:erp/routes/orders.py†L45-L190】【F:erp/routes/tenders.py†L1-L120】
4. Gate unfinished report builder routes behind feature flags and ship the promised UI or hide the navigation until the persistence layer exists.【c655b7†L11-L44】【0358e2†L10-L12】
5. Publish Celery/Redis operator playbooks (scaling guidance, broker settings, failure modes) to close the integration documentation gap.【0358e2†L3-L12】

Scores will be revisited once these remediation items land on `main`.
