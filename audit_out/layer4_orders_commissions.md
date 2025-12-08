# Layer 4 Audit – Orders, Approvals, Commission Logic

## Scope
Review of order creation/update flows, approvals, commission handling, initiator tracking, and alignment with sales rep vs client initiation requirements.

## Current Capabilities
- **Order creation with initiator typing**: `/orders` POST requires items, reserves inventory, tracks initiator type (`client`, `employee`, `management`), and allows assigning a sales rep; commission flags/rate are captured per order with defaults when provided. Client-initiated commissions must be explicitly approved by management before submission is accepted.【F:erp/routes/orders.py†L52-L173】
- **Geo-tagged order capture**: Order submissions now require `geo_lat`/`geo_lng` with optional accuracy, persist recorder/timestamp, and return geo metadata via the serializer for downstream dashboards and audits.【F:erp/routes/orders.py†L15-L118】【F:erp/models/order.py†L32-L70】
- **Commission state tracking**: Orders persist `commission_enabled`, `commission_rate`, `commission_status`, `commission_approved_by_management`, and `commission_block_reason` fields exposed via serialization for downstream settlement logic.【F:erp/routes/orders.py†L20-L39】【F:erp/models/order.py†L23-L79】
- **Order updates and payments**: PATCH endpoint enforces valid status/payment transitions, toggles commission enablement with optional management approval, and validates commission rate numerics; activity logs capture changes with commission metadata for auditability.【F:erp/routes/orders.py†L175-L245】
- **Supervisor/Admin approvals gated by MFA-aware roles**: Approval listing and decisions now require privileged roles (`manager`, `admin`, `supervisor`) guarded by MFA-aware decorators, reducing the risk of unverified sessions approving orders.【F:erp/routes/approvals.py†L12-L74】【F:erp/security.py†L60-L118】

## Gaps & Risks vs. Requirements
- **Approval workflow incomplete**: Order submission still lacks a full supervisor/admin approval lifecycle (dual-control, SLA, delivery sign-off) even though decision endpoints now enforce privileged, MFA-aware roles.【F:erp/routes/orders.py†L128-L188】【F:erp/routes/approvals.py†L12-L74】
- **Commission eligibility logic partially covered**: Commission status now blocks client-initiated commissions without management approval and marks credit sales as pending until payment settlement, but still lacks monthly payout rollups, credit-term enforcement, and performance-ledger reporting.【F:erp/routes/orders.py†L20-L245】【F:erp/models/order.py†L52-L79】
- **Role separation and MFA**: Order creation/edit endpoints are still guarded primarily by `sales`/`admin`; supervisor role differentiation, and MFA for commission overrides, are only partially covered by the approvals layer.【F:erp/routes/orders.py†L52-L237】【F:erp/routes/approvals.py†L12-L74】
- **Geo and SLA gaps**: Order creation is now geo-stamped, but delivery/hand-off geo confirmations plus SLA timers/escalations for unfulfilled or delayed orders are still missing.【F:erp/routes/orders.py†L52-L237】
- **UI/UX modernization**: No modern order intake/review UI described (status trackers, filters, mobile-friendly forms), and no client dashboard to initiate orders or view progress with commission transparency where applicable.

## Recommendations
1. **Add approval pipeline**: Introduce supervisor/admin approval states (e.g., pending_approval → approved → fulfilled) with audit logs, MFA prompts, and role checks; surface in UI dashboards with filters and responsive design.
2. **Implement commission engine**: Calculate commission_amount based on rate and paid invoices; defer payment until settlement for credit sales, and disable commission when client-initiated unless management assigns a rep/override. Add monthly rollups and payout reports per sales rep.
3. **Enforce role separation**: Restrict commission enablement/rate edits to supervisors/admins with MFA; limit order creation for sales reps while allowing clients via client portal, applying policy-based RBAC.
4. **Geo + SLA tracking**: Capture geo metadata for order creation/delivery confirmation; implement SLA timers/escalations for unfulfilled orders and delivery delays, with alerts to management.
5. **UX upgrades**: Build modern order intake/review experiences with status timelines, bulk actions, validation hints, accessibility, and mobile-ready layouts for clients and employees.
