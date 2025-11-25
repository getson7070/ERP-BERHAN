# F10 — Security Hardening & Identity Defense

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
