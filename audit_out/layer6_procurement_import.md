# Layer 6 Audit – Procurement & Import Tracking

## Scope
Review procurement purchase orders, milestones, landed cost capture, ticketing, and approval flows versus required import tracking, SLA, geo capture, and supervisor visibility.

## Current Capabilities
- **Purchase orders with lines and totals**: `/api/procurement/orders` supports creation and listing with supplier, currency, and line detail, recalculating totals and linking to tickets when provided.【F:erp/procurement/routes.py†L135-L200】
- **Ticket linkage with SLA + milestones**: Procurement tickets expose SLA breach evaluation, escalation level, and milestone tracking, returned with order and ticket serializers for monitoring import steps.【F:erp/procurement/routes.py†L88-L127】
- **Role-gated submissions/approvals**: Procurement APIs require `procurement`, `inventory`, or `admin` roles for list/create/submit/approve/cancel endpoints, aligning with RBAC for procurement staff.【F:erp/procurement/routes.py†L135-L200】
- **Geo-located milestones**: Milestones now persist latitude/longitude, accuracy, recorder, and timestamp and enforce location for completed events so custody checkpoints are auditable.【F:erp/procurement/models.py†L181-L213】【F:erp/procurement/routes.py†L65-L122】【F:erp/procurement/routes.py†L565-L613】

## Gaps & Risks vs. Requirements
- **Import milestone depth**: Milestones exist but lack predefined templates for import stages (shipping, customs, clearance, delivery) and do not auto-update geo/location checkpoints or ETA changes.
- **Supervisor approval separation + MFA**: No dedicated supervisor lane or MFA enforcement for approvals/rejections of procurement tickets or orders; requirements call for management supervisor and admin with second factor.
- **Landed cost/commission alignment**: Landed cost totals exist on tickets, but allocation into inventory/finance and linkage to commission eligibility for import-driven sales is unspecified.
- **Geo capture and audit trails**: Procurement actions beyond milestone creation (e.g., approvals/receipts) still lack geo metadata or device context; requirement wants geo logging on approvals and visits.
- **UX/visibility**: No modern UI surfaced for procurement dashboards with Kanban/ETA views, SLA breach highlighting, or mobile-ready updates; needs contemporary UX refresh.

## Recommendations
1. **Define import milestone templates** with statuses, expected durations, and auto SLA rules; integrate geo checkpoints and ETA recalculation from location pings.
2. **Enforce supervisor + MFA approvals** on submit/approve/cancel endpoints; add per-role approval thresholds and audit logs with device/geo metadata.
3. **Landed cost posting flow** to push allocated costs into inventory/finance and flag commissions based on final landed costs when linked to sales orders.
4. **Geo + audit middleware** for procurement endpoints to capture lat/lng/IP and actor; emit structured events for observability and alerts.
5. **Modern procurement UI**: responsive dashboards (table + Kanban + timeline), SLA breach badges, and inline milestone updates; ensure accessibility and offline-friendly interactions.
