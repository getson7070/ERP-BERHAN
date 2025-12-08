# Layer 5 Audit – Maintenance Workflow, Geo, SLA & Escalation

## Scope
Evaluation of maintenance asset/work-order flows, geo capture, SLA/escalation rules, and alignment with required tracking and management alerts.

## Current Capabilities
- **Asset and schedule management**: Maintenance API supports asset CRUD (with depreciation metadata) and schedules per asset, restricted to maintenance/admin roles and scoped by org.【F:erp/routes/maintenance_api.py†L60-L149】
- **Geo-aware work orders**: Work-order creation accepts request geolocation, records events with geo lat/lng, and supports role-gated creation for maintenance/admin/dispatch/client/sales/marketing personas.【F:erp/routes/maintenance_api.py†L322-L359】
- **Technician start/check-in with geo logging**: Start and check-in endpoints capture geo coordinates, record events, and update SLA evaluations, ensuring geo trail for on-site actions.【F:erp/routes/maintenance_api.py†L397-L476】
- **SLA and escalation engine**: `_run_sla_evaluations` raises escalation events for overdue due dates and downtime thresholds, logging audit/activity events with rule metadata and updating `sla_status`.【F:erp/routes/maintenance_api.py†L232-L319】

## Remediation delivered in this update
- Geo coordinates are now required (and validated) for work-order start and technician check-ins so SLA and audit trails always include a location signal. Numeric validation prevents malformed payloads and returns actionable 400 responses when geo is missing.【F:erp/routes/maintenance_api.py†L382-L437】
- Work-order serialization now surfaces SLA due timestamps/minutes remaining, and a new responsive maintenance dashboard (`/maintenance/work_orders.html`) visualizes status, priority, SLA, and geo coverage for supervisors and technicians.【F:erp/routes/maintenance_api.py†L155-L178】【F:templates/maintenance/work_orders.html†L1-L236】

## Gaps & Risks vs. Requirements
- **Supervisor approval and visibility**: Maintenance creation/updates lack supervisor/admin approval gates and dashboards; escalation rules trigger silently without management acknowledgment flows or MFA prompts for overrides.【F:erp/routes/maintenance_api.py†L322-L476】
- **Geo requirements not end-to-end**: While geo is captured for work orders, there is no enforcement for employee access events, scheduled visits logging, or delivery/maintenance completion confirmation by clients with location proof.【F:erp/routes/maintenance_api.py†L322-L476】
- **SLA coverage**: SLAs focus on due dates/downtime but omit response-time SLAs, technician arrival confirmation, and multi-channel notifications/queues for escalations. No UI to configure SLA rules or visualize breaches.【F:erp/routes/maintenance_api.py†L232-L319】
- **Commission/role alignment**: Maintenance flows permit creation by many roles but do not tailor permissions for supervisors vs admins or integrate with sales commission or HR performance tracking for maintenance tasks.【F:erp/routes/maintenance_api.py†L322-L476】
- **UI/UX modernization**: No evidence of modern maintenance dashboards (map-based views, timeline/status, mobile-friendly checklists, offline support). Client complaint/help visibility is not integrated with maintenance tickets.

## Recommendations
1. **Add supervisor-led approvals**: Require supervisor/admin approval for critical/priority work orders and SLA overrides, with MFA and audit trails; surface pending items in a responsive management console.
2. **Expand geo verification**: Enforce geo capture for technician arrival/completion and client confirmations; add geo fences and tamper checks. Log geo metadata to audit tables and surface on map/timeline views.
3. **Broaden SLA model**: Include response-time SLAs, technician arrival windows, reminder/escalation channels (email/SMS/Telegram), and a UI to configure rules and visualize SLA status and escalations.
4. **Role and performance linkage**: Align maintenance permissions with supervisor vs admin roles; feed work-order completion and SLA adherence into HR performance and analytics dashboards; ensure commission/credit policies are unaffected by maintenance roles.
5. **UX upgrades**: Build modern maintenance and client-help/complaint portals with status timelines, map overlays, accessibility compliance, offline-capable mobile checklists, and real-time alerts for overdue or stalled work.
