# F10 — Security Hardening & Identity Defense

This blueprint layers on top of the 21-task upgrade and F1–F9. It keeps existing RBAC, CSRF, CI/CD, and bot/reporting fabrics intact while adding identity rigor, pervasive permission enforcement, and tamperproof auditability so stolen passwords or URLs cannot quietly compromise Inventory, Orders, or Reports.

---

## Ripples of protection
1. **Stronger identities** – passwords alone are insufficient (MFA, device trust, disciplined sessions).
2. **Permission coverage everywhere** – no HTTP route, Celery task, CLI, bot command, or internal API runs without an explicit guard.
3. **Provable actions** – every sensitive change is attributable to a role, org, and cryptographic proof.

---

## 1) Strong Identity: MFA, device trust, and session discipline
**What to add**
- **TOTP MFA** for admins, finance/banking approvers, inventory supervisors, and anyone touching Orders/Inventory/Reports.
- Modules: `erp/auth/mfa_service.py` (generation/validation) and `erp/auth/routes_mfa.py` (enrolment, verification, backup codes), backed by a per-user/org `user_mfa_settings` table.
- **Trusted device flags** (cookie + UA + partial IP hash): first login from a new device forces MFA; optionally remember devices for X days.
- **Session rotation**: short access token TTL (≈15–30 minutes) and refresh-token rotation on role change, password reset, or suspicious activity.

**Interaction with current app**
- Keep existing login and JWT/session flow; add MFA as a second step for high-privilege roles and extend refresh logic with rotation hooks.

**Expert challenges to resolve**
- Who must have mandatory MFA (all inventory/finance staff vs. admins only)?
- What fallback (backup codes/hardware keys) is acceptable for users without authenticator apps?
- How short can sessions be before UX degrades and users start unsafe behaviors (shared logins, pinned sessions)?

---

## 2) Deep RBAC enforcement: no unprotected path
**What to add**
- **Central permission registry** per resource/action (e.g., `inventory.adjust_stock` → `write|approve|export`, allowed roles per org).
- **Mandatory decorators** on every entrypoint: `@require_permission`, `@require_task_permission`, `@require_cli_permission`, `@require_bot_permission`.
- **CI scanner** that fails if a route/task/bot handler lacks a guard or mis-maps a permission, extending existing registry scans.

**Expert challenges to resolve**
- Migration plan for legacy endpoints without guards.
- Blast radius if a decorator is misconfigured—how to avoid mass lockout?
- Ownership model for per-org permission variants vs. global defaults.

---

## 3) Data-level safety: org boundaries and ownership
**What to add**
- **Scoped ORM helpers** (e.g., `scoped_query(model, user)` filtering by `org_id`) for Inventory/Orders/Reports/Finance; ban naked `.query` in those modules.
- **Ownership checks** on critical objects (order org/assignee/region vs. current user role).
- Optional **soft partitioning / Postgres RLS**; ensure new tables carry `org_id` plus indexes on `(org_id, …)`.

**Expert challenges to resolve**
- RLS everywhere vs. disciplined app-level scoping.
- Guarantees that raw SQL paths are covered (tests/fuzzers for cross-org leakage).

---

## 4) Secrets, tokens, and crypto hygiene
**What to add**
- Central crypto helper `erp/security/crypto.py` for HMAC/JWT helpers, secure randoms, and key lookup by `kid`.
- **Key IDs and rotation grace periods** for JWT, banking signatures, bot tokens; target 90-day rotation with rollback plan.
- Source of truth for key metadata (Vault/env/DB) plus documented rollback on failed rotation.

**Expert challenges to resolve**
- Managing multiple active keys during cutover.
- Ensuring clients/banks handle `kid` and rotated secrets without downtime.

---

## 5) Banking, bots, and webhooks: trust but verify
**What to add**
- **Inbound signing**: require HMAC/PK signature header (e.g., `X-Signature`) for banking callbacks, bot webhooks, third-party events.
- **Outbound signing** for payments/statement requests; log signature metadata for audit.
- **Replay/idempotency**: extend the `BotIdempotencyKey` pattern to payments, confirmations, and high-impact approvals.

**Expert challenges to resolve**
- Align signing scheme and clock-drift handling with each bank/integration.
- Log enough context to detect replays and signature failures without exposing secrets.

---

## 6) Security telemetry: see attacks early
**What to add**
- Metrics for login/MFA failures by user/IP/device; permission-denied events per module; spikes in inventory adjustments, order cancellations, price overrides, and report exports.
- Export to Prometheus; send severe anomalies to Sentry and into incident runbooks.
- Balance alerting to avoid fatigue; define owners and review cadence for dashboards.

---

## 7) Rollout ripples
1. **Next 3 weeks** – MFA for high-privilege roles; decorators + scoped queries on Inventory/Orders/Reports.
2. **Next 3 months** – Permission registry stable; webhook signing and token rotation live; incidents shift from security to UX concerns.
3. **Next 3 years** – Bank-grade posture: provable, tamper-resistant trails for regulators/partners; bigger clients onboard safely.

**Hidden contract**: every new feature must answer
- Which identity is acting?
- Which permission is exercised?
- Which org’s data is touched?
- Which key/signature proves legitimacy?

Embedding these questions into templates, decorators, CI checks, and reviews keeps security a default—not a one-time project.
This blueprint layers on top of the 21-task upgrade and F1–F9. It focuses on strong identity, pervasive permission enforcement, org-level data safety, secrets/crypto hygiene, trusted integrations, and security telemetry. All items are additive and avoid breaking existing flows.

## Objectives
- Strengthen identities with MFA, device trust, and disciplined sessions so leaked passwords alone are insufficient.
- Enforce permissions on every surface (HTTP, bots, tasks, CLI) and prevent cross-org access.
- Cryptographically protect tokens and integrations with rotation-ready keys and signed requests.
- Detect and surface security anomalies early with dedicated telemetry.

## A. Strong Identity (MFA, Devices, Sessions)
- Add TOTP-based MFA for admins, finance approvers, inventory supervisors, and anyone touching Orders/Inventory/Reports.
- Implement `erp/auth/mfa_service.py` and `erp/auth/routes_mfa.py` with enrolment, verification, backup codes, and per-user/org MFA settings.
- Track trusted devices (cookie + UA + partial IP hash); force MFA on new devices, optionally remember for X days.
- Shorten access token TTL (15–30 minutes); rotate refresh tokens on role change, password reset, or suspicious activity.

## B. Deep RBAC Coverage
- Central permission registry: resource (e.g., `inventory.adjust_stock`, `orders.create`, `reports.finance_pnl`), action (`read|write|approve|export`), allowed roles per org.
- Mandatory decorators for all entrypoints: `@require_permission`, `@require_task_permission`, `@require_cli_permission`, `@require_bot_permission`.
- CI scanner fails when routes/tasks/bot handlers lack guards or mismap permissions, extending prior registry scans.

## C. Data-Level Safety & Org Boundaries
- Route ORM access via scoped helpers (e.g., `scoped_query(model, user)` filtering by `org_id`); ban naked `.query` in Inventory/Orders/Reports/Finance.
- Enforce ownership checks on critical objects (order org/assignee/region vs. current user role).
- Optional Postgres RLS or strict app-level filters; ensure new tables include `org_id` plus indexes on `(org_id, ...)`.

## D. Secrets, Tokens, and Crypto Hygiene
- Centralize crypto in `erp/security/crypto.py` for HMAC/JWT helpers, secure randoms, and key lookup by `kid`.
- Maintain key IDs and support rotation grace periods for JWT, banking signatures, and bot tokens; document 90-day rotation policy.
- Store key metadata in Vault/env/DB as appropriate; plan rollback if new keys fail.

## E. Trusted Integrations & Webhooks
- Require inbound webhook signatures (e.g., `X-Signature`) for banking callbacks, bot webhooks, and third-party events; verify with shared secret or public key.
- Sign outbound banking/payment requests; log signature metadata for audit.
- Extend idempotency/replay protection (pattern from `BotIdempotencyKey`) to payments, confirmations, and approvals.

## F. Security Telemetry & Alerts
- Track login/MFA failures by user/IP/device, permission-denied rates per module, spikes in inventory adjustments, order cancellations, price overrides, and report exports.
- Export metrics to Prometheus; send high-severity anomalies to Sentry and incident runbooks.
- Balance alerting to avoid fatigue; define review cadence/owner for security dashboards.

## G. Rollout & Operational Considerations
- Phase 1: enable MFA for high-privilege roles; add decorators and scoped queries on Inventory/Orders/Reports first.
- Phase 2: turn on webhook signing and token rotation; enforce CI guardrails for permission coverage.
- Phase 3: expand MFA to broader roles, enable RLS/app-level filters everywhere, and monitor telemetry dashboards weekly.
- Document ownership: who manages role→permission mapping, key rotation, and response to failed signatures or RBAC denials.

## Open Questions to Finalize
- Which roles/orgs must have mandatory MFA vs. optional? What are acceptable device-trust durations?
- Do we allow per-client customization of role→permission mappings, or keep a global policy with limited overrides?
- Will we adopt Postgres RLS universally, or rely on application-level scoping with periodic cross-org leak tests?
- What is the process/owner for key rotation failures and webhook signature disputes?
