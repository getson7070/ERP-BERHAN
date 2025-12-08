# Layer 4 Audit – Orders, Approvals, Commission Logic

## Scope
Review of order creation/update flows, approvals, commission handling, initiator tracking, and alignment with sales rep vs client initiation requirements.

## Current Capabilities
- **Order creation with initiator typing**: `/orders` POST requires items, reserves inventory, tracks initiator type (`client`, `employee`, `management`), and allows assigning a sales rep; commission flags/rate are captured per order with defaults when provided.【F:erp/routes/orders.py†L52-L163】
- **Commission state tracking**: Orders persist `commission_enabled`, `commission_rate`, `commission_status`, and `commission_amount` fields exposed via serialization for downstream settlement logic.【F:erp/routes/orders.py†L20-L37】
- **Order updates and payments**: PATCH endpoint enforces valid status/payment transitions, toggles commission enablement, and validates commission rate numerics; activity logs capture changes with commission metadata for auditability.【F:erp/routes/orders.py†L172-L237】

## Gaps & Risks vs. Requirements
- **No approval workflow**: Order submission sets status `submitted` but there is no supervisor/admin approval step, SLA, or dual-control before fulfillment/payment—conflicts with requirement for management/supervisor approvals for orders and deliveries.【F:erp/routes/orders.py†L128-L188】
- **Commission eligibility logic missing**: Commission status is stored but not recomputed based on payment settlement or initiator rules (2% monthly, blocked for credit until settled, disabled when client-initiated unless management overrides). No linkage to sales rep performance or payout schedule.【F:erp/routes/orders.py†L20-L237】
- **Role separation and MFA**: Only `sales`/`admin` roles guard endpoints; supervisor vs admin distinction and MFA for commission overrides/approvals are absent.【F:erp/routes/orders.py†L52-L237】
- **Geo and SLA gaps**: Order flow does not capture geo context for initiators or deliveries, nor SLA timers or escalation for unfulfilled orders, contrary to tracking requirements.【F:erp/routes/orders.py†L52-L237】
- **UI/UX modernization**: No modern order intake/review UI described (status trackers, filters, mobile-friendly forms), and no client dashboard to initiate orders or view progress with commission transparency where applicable.

## Recommendations
1. **Add approval pipeline**: Introduce supervisor/admin approval states (e.g., pending_approval → approved → fulfilled) with audit logs, MFA prompts, and role checks; surface in UI dashboards with filters and responsive design.
2. **Implement commission engine**: Calculate commission_amount based on rate and paid invoices; defer payment until settlement for credit sales, and disable commission when client-initiated unless management assigns a rep/override. Add monthly rollups and payout reports per sales rep.
3. **Enforce role separation**: Restrict commission enablement/rate edits to supervisors/admins with MFA; limit order creation for sales reps while allowing clients via client portal, applying policy-based RBAC.
4. **Geo + SLA tracking**: Capture geo metadata for order creation/delivery confirmation; implement SLA timers/escalations for unfulfilled orders and delivery delays, with alerts to management.
5. **UX upgrades**: Build modern order intake/review experiences with status timelines, bulk actions, validation hints, accessibility, and mobile-ready layouts for clients and employees.
