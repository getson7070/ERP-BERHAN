# ERP-BERHAN Main Branch Update Plan

## Objectives
1. Close the five audit findings from `audit_out/main_branch_audit.md` with production-ready fixes that preserve tenant isolation, RBAC, UI/UX polish, and operational resiliency.
2. Align UI/UX, database, and logging behavior with industry standards, ensuring all affected modules remain compatible with existing deployments.
3. Establish verification hooks (tests, smoke checks, and observability alerts) so the remediations remain enforceable.

## Workstream 1 — Harden runtime secrets & database configuration
- **Design**: Update `erp/__init__.py` and related factory helpers so missing `SECRET_KEY` or `DATABASE_URL` raise `RuntimeError`. Wire default config to pull managed secrets via environment or vault adapters.
- **Implementation steps**:
  1. Refactor the Flask app factory to import validated settings from `config.py` rather than reimplementing fallbacks.
  2. Add CI pytest covering app init when env vars are absent (should fail) and when valid env vars are set (should pass).
  3. Extend `docker-compose*.yml` and Helm/ops manifests so all services pass managed secrets.
- **Security/Compatibility checks**: Confirm new behavior doesn’t break local dev by providing `.env.example` and docs describing how to set secrets locally; add backwards-compatible upgrade guidance in `README_UPGRADE_87.md`.

## Workstream 2 — Secure self-service registration and UI flows
- **Design**: Convert `/auth/register` into an invite/approval workflow with server-side role whitelisting.
- **Implementation steps**:
  1. Add CSRF tokens to `templates/login.html` and other onboarding templates using Flask-WTF.
  2. Implement rate limiting + MFA hooks before activating privileged roles.
  3. Update `/auth/register` to queue requests for admin approval and restrict selectable roles in the UI.
  4. Refresh UI copy/error states so the experience matches industry UX expectations (responsive layout, inline validation,
     accessibility labels).
- **Security/Compatibility checks**: Write integration tests covering CSRF enforcement, unauthorized role escalation, and UI snapshot tests; document migration steps for existing self-service tenants in `README.md`.

## Workstream 3 — Move audit logs into durable, centralized storage
- **Design**: Replace `erp/audit.py` SQLite writer with SQLAlchemy models persisted in PostgreSQL (or streaming to the observability pipeline).
- **Implementation steps**:
  1. Define `AuditEvent` model + Alembic migration with partitioning/retention metadata.
  2. Wire audit helper to reuse app DB sessions and emit structured logs to OpenTelemetry/Prometheus exporters.
  3. Update backup/restore docs to include audit tables; add health checks verifying audit inserts succeed.
- **Security/Compatibility checks**: Add unit tests verifying audit writes fail closed and data is immutable; ensure migrations run idempotently across staging/prod.

## Workstream 4 — Restore database automation & resilience drills
- **Design**: Recreate the missing `scripts/index_audit.py` and disaster-recovery drills or update docs to point at modern equivalents under `tools/`.
- **Implementation steps**:
  1. Author new scripts under `tools/db/` to run index health checks, PITR validation, and replication lag monitors.
  2. Reference the scripts from `DATABASE.md`, `README-DEPLOY.md`, and CI workflows (nightly job invoking the scripts).
  3. Capture expected outputs/log retention policies so operators can prove compliance.
- **Security/Compatibility checks**: Ensure scripts respect managed identity creds and support both on-prem and cloud Postgres; add smoke tests against dockerized DB in CI.

## Workstream 5 — Implement permission matrix & RBAC enforcement
- **Design**: Finish `erp/security_gate.py` by mapping roles to permissions stored in DB/config; enforce checks in blueprints.
- **Implementation steps**:
  1. Create `permissions` table + seeding scripts describing capabilities (CRUD per module).
  2. Update `require_permission()` decorator to consult cache-backed lookup + tenant scoping via `resolve_org_id()`.
  3. Add regression tests ensuring unauthorized users receive HTTP 403 and audit events are emitted.
- **Security/Compatibility checks**: Document default role mappings and migration steps; ensure backward compatibility by providing a safe default for legacy roles until they’re migrated.

## Cross-cutting quality gates
- **UI/UX validation**: Run automated Lighthouse/axe-core audits for onboarding/auth forms; capture screenshots for approvals.
- **Security testing**: Expand pytest suite with CSRF, rate limiting, and RBAC tests; schedule quarterly penetration tests covering registration and audit-log tampering scenarios.
- **Database standards**: Enforce schema linting via `alembic check` and `sqlfluff`; keep backups in CI using `init_db.py` + new automation scripts.
- **Documentation & training**: Update `README.md`, `SECURITY.md`, `DATABASE.md`, and runbooks so operators know how to configure secrets, review registrations, and monitor audit pipelines.
- **Deployment sequencing**: Roll out fixes in order (Workstreams 1 & 2 first, then 3, 5, 4) with feature flags allowing staged enablement; include rollback instructions per environment.

## Verification & sign-off
1. All new tests and linting jobs must pass in CI (unit, integration, UI, DB scripts).
2. Security team reviews the RBAC and audit logging implementations before production deploy.
3. Product/design sign off on the refreshed onboarding experience to confirm it meets industry-standard UX.
4. Update `audit_out/main_branch_audit.md` with remediation evidence once each workstream ships.
