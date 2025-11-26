# F4 – Centralised Access Surfaces & RBAC Enforcement

This blueprint strengthens application-wide access control so every surface (HTTP, API, bot, webhook, CLI, Celery) consistently enforces tenant scoping, authentication, and permissions without bypasses. Changes are additive and aligned with prior RBAC upgrades.

## Objectives
- Route all access through a unified gatekeeper that supplies org context and permission checks.
- Enumerate and secure every access surface to prevent hidden backdoors.
- Centralise permission codes and role mappings to eliminate scattered string checks.
- Apply RBAC to background jobs, webhooks, and bots—not just web routes.

## Gatekeeper pattern
- Maintain `erp/security_gate.py` as the single entrypoint for authz/tenant context.
- Provide helpers:
  - `get_gate()` for user-driven requests (derives user + org from session/JWT).
  - `get_system_gate(org_id)` for trusted system actors (workers/schedulers) with scoped permissions.
- Methods:
  - `require_perm(perm_code)` enforces role → permission mapping.
  - `current_org()` returns resolved tenant ID to avoid ad-hoc `current_user.org_id` access.
- Views/tasks obtain org via the gate; direct DB access without scoping is disallowed.

## Access surfaces to harden
Document in `docs/security/access_surfaces.md` (or similar) and enforce in code:
1. **HTTP web app** – session/JWT auth; gate determines org and perms.
2. **JSON/API** – token/JWT; per-route permission and org scoping.
3. **CLI/management commands** – require explicit `--org` and system gate checks.
4. **Celery/cron tasks** – run under `SystemGate` with minimal perms per task.
5. **Webhooks/bots** – authenticate via HMAC/token; map webhook/bot to org; enforce dedicated system permission (e.g., `perm.BANK_WEBHOOK`).

## Central permission mapping
Create/extend `erp/security/permissions.py`:
- Define constants: `INVENTORY_VIEW`, `INVENTORY_EDIT`, `ORDERS_CREATE`, `ORDERS_OVERRIDE_STOCK`, `REPORT_FINANCE_VIEW`, etc.
- Map roles to permission sets (e.g., `ROLE_SALES`, `ROLE_INVENTORY`, `ROLE_FINANCE`, `ROLE_EXEC`).
- The gate reads this mapping; routes/tasks reference constants, not raw strings.

## RBAC coverage tests
Add `tests/security/test_access_surfaces.py` to verify:
- Routes without the required permission return 403; with permission succeed.
- Celery/CLI tasks fail fast without system gate permissions.
- Webhooks with invalid signature/token are rejected (401/403) and never processed.
- Multi-tenant isolation: users from Org A cannot access Org B resources.

## Observability
- Log access decisions with user/org, surface, permission checked, and outcome (allow/deny) without leaking sensitive data.
- Metrics: counters for denies by reason (missing perm, missing org, bad signature); alerts on unusual deny spikes that may signal abuse.

## Rollout plan
1. **Inventory routes first**: wrap inventory/stock-related endpoints with gate + permission constants.
2. **Orders & reporting**: align create/update/approve flows and report endpoints with gate checks, respecting F2/F3 RBAC rules.
3. **Bots/webhooks/CLI**: migrate integrations and scripts to use system gate helpers and tokens/HMAC.
4. **Enforcement audit**: add a lint/test to ensure every registered route/task declares a permission or explicit allowlist.

## Open policy questions
- Should routes/tasks declare a single required permission or allow composite policies (e.g., A or B)? Gate API must support chosen policy.
- Will external third parties access APIs? If yes, add per-client tokens, scopes, and rate limits.
- Who is authorised to change role → permission mappings (central admin only, or delegated via UI)? Policy affects where mappings live (code vs DB).

## Security posture
- Enforce tenant scoping via gate on **every** DB query path.
- No “god mode” tasks; system tasks use minimal required permissions.
- Keep secrets (tokens/HMAC keys) in environment/secret store; never commit.
