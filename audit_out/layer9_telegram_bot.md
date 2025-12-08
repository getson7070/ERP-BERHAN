# Layer 9 Audit – Telegram Bot & Automation

## Scope
Evaluate Telegram/automation handlers for approvals, inventory, analytics, and integration depth with workflow/RBAC requirements.

## Current Capabilities
- **Command handlers for approvals/inventory/analytics**: Bot handlers provide approve/reject responses, inventory summaries, and top performance scores via analytics queries, enabling lightweight chat interactions.【F:erp/bots/handlers.py†L1-L58】
- **Intent mapping**: NLP intents map analytics keywords to the analytics handler, showing extendable intent-based automation surface for future flows.【F:erp/bots/nlp_intents.py†L1-L34】

## Gaps & Risks vs. Requirements
- **Workflow execution**: Handlers return static text; they do not execute real approval, order, maintenance, or procurement actions with audit/RBAC checks.
- **MFA/role enforcement**: Bot commands do not enforce supervisor/admin MFA or role validation; risk of unauthorized actions if extended.
- **Geo/context capture**: Bot actions do not record geo/IP/device context or link to order/maintenance tickets; requirement expects geo-aware approvals/visits.
- **UI/UX and notifications**: No rich formatting, buttons, or notification routing (per-role channels, SLA breaches) to meet modern UX expectations.
- **Security hardening**: Token rotation, rate limiting, and tenant scoping were previously undocumented; webhook requests now require a configured secret, known chat binding, and optional per-bot chat allowlists, but we still need scoped JWT/session tokens before executing privileged workflows.

## Recommendations
1. **Bind commands to real workflows** with secure API calls for approvals, order status, maintenance updates; enforce RBAC and audit logging per tenant.
2. **Add MFA/OTP challenge** for privileged actions and supervisor/admin roles; consider per-session signing or deep links with short-lived tokens.
3. **Context + geo capture** on bot actions, linking to underlying tickets/orders and storing metadata for audit.
4. **UX improvements**: Inline keyboards, rich status cards, SLA breach notifications, and per-role routing (client/employee/supervisor/admin channels).
5. **Security/operations**: Enforce webhook signature validation, rate limiting, token rotation, and monitoring; document tenant isolation and error handling.
