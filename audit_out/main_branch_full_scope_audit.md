# ERP-BERHAN main branch audit — production readiness & control layers (2025-02-14)

## Scope & methodology
- Reviewed factory/deployment assets (`erp/__init__.py`, `README-DEPLOY.md`) plus operational guides (`DATABASE.md`, tooling under `tools/`).
- Inspected customer-facing UX templates (`templates/login.html`) and blueprints powering dashboards, analytics, reports, approvals, orders, bots, and automation hooks (`erp/routes/*.py`, `erp/blueprints/*.py`).
- Evaluated centralized RBAC helpers (`erp/security.py`, `erp/security_gate.py`, `erp/utils/core.py`) and durable logging primitives (`erp/audit.py`, `erp/models/audit_log.py`).
- Exercised the existing automated tests that guard auth and CSRF enforcement (`pytest tests/test_auth_queries.py -k auth --maxfail=1` and `pytest tests/test_csrf_presence.py`).

## Production readiness & deployment status
- The application factory now enforces explicit `SECRET_KEY`/`DATABASE_URL` configuration and ships hardened session/cookie defaults while capping self-registration roles, preventing unsafe production boots unless operators opt into `ALLOW_INSECURE_DEFAULTS` for dev use.【F:erp/__init__.py†L43-L115】
- Blueprint registration is declarative and deduplicated, ensuring finance, CRM, HR, supply chain, analytics, dashboards, and maintenance modules are consistently mounted before deployment freezes blueprint lists.【F:erp/__init__.py†L118-L199】
- `README-DEPLOY.md` documents the supported docker-compose pipeline, blueprint freezing workflow, and migration cadence so staging/production parity stays repeatable; DB snapshot automation is captured for operators as well.【F:README-DEPLOY.md†L1-L41】

## Database resilience, logging, and analytics data quality
- `DATABASE.md` codifies index audits, RPO/RTO objectives, and backup verification, tying into the documented `tools.index_audit`/`tools.backup_drill` scripts that fail CI when critical indexes (audit, finance, orders, RBAC) disappear or backups stop producing manifests.【F:DATABASE.md†L5-L33】【F:tools/index_audit.py†L1-L85】
- Finance, maintenance, CRM, analytics, approvals, and supply chain models share UTC-aware timestamp mixins and geo fields so dashboards/alerts align across tenants while audit logging persists tamper-evident hash chains in `audit_logs`.【F:erp/models/core_entities.py†L1-L94】【F:erp/audit.py†L1-L52】【F:erp/models/audit_log.py†L1-L24】

## Dashboard, reporting, geolocation & UX polish
- The analytics blueprint computes monthly sales, maintenance load, CRM pipeline totals, and geo hotspot tallies, emitting the `/analytics/dashboard` JSON consumed by the UI and powering reminders/forecasting helpers.【F:erp/routes/analytics.py†L24-L169】
- The report builder aggregates finance credits/debits, CRM funnel counts, low-stock alerts, maintenance tickets, shipments, and geolocation clusters to provide cross-module KPIs for operators.【F:erp/routes/report_builder.py†L1-L96】
- Login/request-access UX adopts responsive Bootstrap patterns, dual-column onboarding, CSRF tokens, MFA messaging, and accessible alerts so flows meet contemporary industry expectations.【F:templates/login.html†L3-L83】

## User management, centralized RBAC, approvals, and user logging
- Authentication endpoints enforce rate limits, invite consumption, duplicate-request detection, and post-login redirects while persisting hashed credentials through the canonical `User` model and loader hooks.【F:erp/routes/auth.py†L1-L220】【F:erp/models/user.py†L1-L81】
- Role decorators (`require_roles`, `role_required`) and MFA helpers provide hierarchical gates, yet the new permission-matrix-based `install_global_gate` remains unused anywhere outside its definition, so RBAC is only enforced where decorators are manually added.【F:erp/security.py†L71-L165】【F:erp/utils/core.py†L65-L154】【F:erp/security_gate.py†L44-L141】【845f2†L1-L2】
- Approvals endpoints keep human-in-the-loop (HITL) workflows for order decisions, require login plus manager/admin roles, and emit audit events for every decision, tying approval history into the tamper-evident log chain.【F:erp/routes/approvals.py†L1-L117】【F:erp/audit.py†L1-L52】
- Order creation uses `require_roles("sales", "admin")`, but subsequent status updates only require authentication, allowing any logged-in role to flip order states without RBAC review—this is the remaining gap blocking “all modules under centralized RBAC.”【F:erp/routes/orders.py†L31-L105】

## Geolocation instrumentation & analytics readiness
- Analytics vitals capture latitude/longitude plus city labels, storing them in `AnalyticsEvent` records and surfacing the clusters in dashboard/report payloads, satisfying the geolocation requirement for anomaly tracking.【F:erp/routes/analytics.py†L63-L133】【F:erp/models/core_entities.py†L34-L85】【F:erp/routes/report_builder.py†L53-L94】

## Bots, automation, and integrations
- Slack bot endpoints expose a `/bots/slack/health` check and echo handler gated by configured tokens, while the Telegram webhook blueprint restricts chat IDs to an allowlist and replies via the official Bot API so automated assistants stay scoped.【F:erp/blueprints/bots.py†L1-L38】【F:erp/blueprints/telegram_webhook.py†L1-L37】
- Security gating treats `/bot/*` and `/api/*` as machine endpoints, expecting JWTs and CSRF exemptions to be configured once `install_global_gate` is wired into the factory; today that hook remains TODO, so automation endpoints rely solely on blueprint-level checks.【F:erp/security_gate.py†L13-L141】

## Functional coverage & readiness summary
- The curated blueprint list demonstrates every major module—analytics, dashboards, approvals, finance, CRM, HR, orders, maintenance, supply chain, marketing, inventory—is registered in the main app, aligning with the requested “functions/modules readiness” review.【F:erp/__init__.py†L122-L199】
- Invite tooling and RPO/RTO drills in `tools/create_registration_invite.py`, `tools/index_audit.py`, and `tools/backup_drill.py` keep onboarding and database operations auditable across environments.【F:tools/create_registration_invite.py†L1-L52】【F:tools/index_audit.py†L1-L85】【F:DATABASE.md†L5-L33】

## Key open issues to track
1. **Global RBAC enforcement** – wire `install_global_gate` (or equivalent) into `create_app()` and backfill `require_roles/require_permission` on update/delete endpoints so every module inherits centralized RBAC automatically.【F:erp/security_gate.py†L94-L141】【845f2†L1-L2】
2. **Order status updates bypass role checks** – add `@require_roles("sales", "admin")` (or finer-grained permissions) to `orders.update` to keep approvals/hierarchy decisions from being overwritten by basic users.【F:erp/routes/orders.py†L31-L105】
3. **Automation endpoints still rely on per-route checks** – once the global gate is installed, `/bot/*` hooks will require JWTs; until then, restrict ingress (reverse proxy ACLs) or add decorator-level auth to the Slack/Telegram handlers.【F:erp/blueprints/bots.py†L1-L38】【F:erp/blueprints/telegram_webhook.py†L1-L37】【F:erp/security_gate.py†L13-L141】
