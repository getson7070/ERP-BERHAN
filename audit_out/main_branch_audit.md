# ERP-BERHAN Main Branch Audit — 2025-11-19

## Methodology
- Static inspection of the `main` branch without executing the application or infrastructure provisioning scripts.
- Focused review on authentication, configuration management, audit logging, and operational documentation because they directly influence confidentiality, integrity, availability, and UI/UX flows requested for validation.

## Findings

### 1. Default secrets and SQLite fallbacks persist in the runtime configuration (High)
`erp/__init__.py` falls back to `SECRET_KEY='change-me'` and a local SQLite database whenever environment variables are absent.【F:erp/__init__.py†L62-L85】 This behavior is safe only for local development; if any production pod boots without secrets configured it will reuse the placeholder key and bypass the hardened PostgreSQL settings described in `config.py`. The weakness undermines session confidentiality and tenant isolation.

**Recommendation:** Align the factory with `config.Config` by raising an error when neither `SECRET_KEY` nor `DATABASE_URL` is provided, and add CI smoke tests that fail when insecure defaults are detected during container builds.

### 2. Self-service registration bypasses approval, CSRF, and role protections (High)
The `/auth/register` endpoint lets unauthenticated visitors pick any role—including `admin`—and immediately logs them in without secondary approval, rate limiting, or MFA checks.【F:erp/routes/auth.py†L82-L134】 The companion HTML form omits CSRF tokens entirely, so even basic browser protections are missing despite CSRF being enabled globally.【F:templates/login.html†L18-L60】 Attackers can forge POSTs that provision privileged accounts or trick existing users into unknowingly submitting the registration form.

**Recommendation:** Gate registration behind invite or approval workflows, enforce role whitelists server-side, require CSRF tokens in forms, and add throttling/MFA before activating privileged roles.

### 3. Audit logs are stored in an unauthenticated SQLite file (High)
`erp/audit.py` writes to a standalone SQLite database selected via `DATABASE_PATH` (defaulting to `:memory:`) instead of the primary PostgreSQL cluster.【F:erp/audit.py†L7-L37】 Audit trails therefore live outside backups, RLS policies, and retention tooling, and they silently reset every time the process restarts when no path is configured. This breaks compliance requirements that mandate tamper-evident, durable audit history.

**Recommendation:** Persist audit events through SQLAlchemy in the core database (with partitions and RLS) or emit them to an append-only log service so retention, hashing, and alerting run against durable storage.

### 4. Database operations documentation references missing automation (Medium)
`DATABASE.md` directs operators to run `scripts/index_audit.py` and `scripts/dr_drill.sh` to validate indexing and recovery drills.【F:DATABASE.md†L5-L13】 The repository no longer ships a `scripts/` directory, so those commands cannot run (`rg --files -g 'index_audit.py'` returns no matches).【2079b4†L1-L2】【a80fd9†L1-L2】 This drift makes it impossible to meet the documented RPO/RTO checks.

**Recommendation:** Restore the automation scripts (or update the documentation to point to the current tooling, e.g., `tools/check_alert_budget.py`) and add CI hooks so index audits and backup drills are exercised continuously.

### 5. Permission gates still contain TODO placeholders (Medium)
`erp/security_gate.py` exposes `require_permission()` but the body still contains a TODO comment and returns success regardless of the requested permission.【F:erp/security_gate.py†L34-L43】 Any blueprint that relies on this decorator therefore lacks real authorization checks, undermining the “always check RBAC” goal stated in `AGENTS.md`.

**Recommendation:** Implement the permission matrix (e.g., mapping roles to capabilities stored in the database) and add unit tests that verify protected endpoints raise `403 Forbidden` when unauthorized.

## Next steps
1. Prioritize fixes for the high-severity findings (secrets, registration, audit logging) before enabling new modules in production.
2. After remediation, rerun the blueprint and health audits under `audit_out/` so evidence stays current.
3. Expand UI/UX validation to include CSRF/error states in onboarding screens to satisfy the “industry standard” requirement outlined by stakeholders.
