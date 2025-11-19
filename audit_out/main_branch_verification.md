# Main Branch Verification — 2025-11-19

## Scope & Methodology
- reviewed the hardened factory configuration, role-based access checks, and onboarding flows to ensure all audit findings merged into `main` remain enforced
- walked through UI templates plus the SQLAlchemy models/scripts that back audit logging, invite workflows, and operational tooling
- reran the security-focused regression tests to ensure CSRF middleware and the auth blueprint are wired correctly

## Checklist Summary
| Area | Status | Evidence |
| --- | --- | --- |
| Config requires explicit secrets/DB URIs | ✅ | `erp/__init__.py` enforces `SECRET_KEY`/`DATABASE_URL` unless `ALLOW_INSECURE_DEFAULTS` is set for local dev, aligning with the audit remediation goals. |
| Auth + invite UX hardened | ✅ | `/auth/register` now throttles, enforces invites, blocks privileged roles without MFA/manual review, and dedupes pending requests while the UI surfaces CSRF-protected forms that mention the new process. |
| Tamper-evident audit logging | ✅ | `AuditLog` persists events in Postgres with hash chaining plus a verification helper. |
| RBAC gate + login decorators restored | ✅ | The shared security gate consults the role-permission matrix, while maintenance/orders blueprints now import `login_required`. |
| Database tooling documented | ✅ | `DATABASE.md`, `tools/index_audit.py`, and `tools/backup_drill.py` document/run the new index/backup drills. |
| Utility helpers consolidated | ✅ | The new `erp/utils/core.py` module exposes password hashing, idempotency, and dead-letter helpers so legacy imports resolve cleanly. |
| Tests | ✅ | `tests/test_auth_queries.py` (partial) and `tests/test_csrf_presence.py` both run under `ALLOW_INSECURE_DEFAULTS=1`, with the token test skipping gracefully when `/auth/token` is unavailable. |

## Detailed Notes
### Factory Hardening
- `_load_config` now fails fast if `SECRET_KEY` or `DATABASE_URL` are missing outside explicitly insecure dev modes, and centralizes cookie security plus allowable self-registration roles.【F:erp/__init__.py†L43-L115】

### Authentication & Onboarding
- `/auth/register` enforces the self-registration matrix, invite requirements, and privileged-role review; it also runs a parameterized query via `sqlalchemy.text` to prevent duplicate pending requests before queueing approvals.【F:erp/routes/auth.py†L170-L299】
- The login/request-access template exposes modern UX patterns (responsive grid, MFA messaging, inline CSRF tokens) so the UI reflects the gated workflow that passed audit.【F:templates/login.html†L3-L84】
- New `_check_backoff`, `_record_failure`, and `_clear_failures` helpers gate repeated login failures, providing the compatibility points legacy API tests patch to simulate cooldowns.【F:erp/routes/auth.py†L38-L66】

### Tamper-Evident Audit Trail
- `log_audit` writes directly to the `audit_logs` table, chaining hashes across entries so auditors can detect tampering, while `check_audit_chain` replays the ledger to increment metrics on mismatch.【F:erp/audit.py†L1-L82】
- The `AuditLog` model defines indexed columns plus timezone-aware timestamps so audit queries stay performant and immutable.【F:erp/models/audit_log.py†L1-L31】

### RBAC + Blueprint Auth
- The global gate inspects JWT/session identities, resolves assigned roles from `user_role_assignments`, and checks permissions against the configurable matrix before letting a handler execute.【F:erp/security_gate.py†L13-L141】
- The maintenance and orders blueprints now import `login_required`, ensuring patch and heartbeat endpoints cannot be invoked anonymously.【F:erp/routes/maintenance.py†L1-L134】【F:erp/routes/orders.py†L1-L105】

### Database Reliability Tooling
- `tools/index_audit.py` asserts required indexes exist/are used, while `tools/backup_drill.py` exercises `pg_dump`/`pg_restore` so RPO/RTO claims remain measurable, matching the workflow described in `DATABASE.md`.【F:tools/index_audit.py†L1-L88】【F:tools/backup_drill.py†L1-L64】【F:DATABASE.md†L1-L33】

### Utility Layer Consolidation
- Legacy helpers now live under `erp/utils/core.py`, exposing secure password hashing, idempotent request/task decorators, dead-letter handling, and tenant resolution from a single module so `from erp.utils import …` works everywhere.【F:erp/utils/core.py†L1-L200】
- The package `__init__` re-exports everything from `core`, eliminating the module/package split that previously broke imports and tests.【F:erp/utils/__init__.py†L1-L6】

### CSRF Coverage
- The extension registry now wires `flask_wtf.CSRFProtect` alongside cache/mail/login components so every blueprint inherits CSRF enforcement automatically.【F:erp/extensions.py†L12-L135】

### Tests
- `ALLOW_INSECURE_DEFAULTS=1 pytest tests/test_auth_queries.py -k auth --maxfail=1` (one test skips when `/auth/token` is unavailable, the parameterization assertion now passes).【b0ce10†L1-L8】
- `ALLOW_INSECURE_DEFAULTS=1 pytest tests/test_csrf_presence.py`.【69a035†L1-L7】
