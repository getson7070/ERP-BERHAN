# Requirements-to-code matrix and implementation blueprint

This document maps the clarified client/employee/admin operating model to the current ERP-BERHAN codebase, identifies concrete gaps, and proposes migrations and workflows that stay aligned with the existing RBAC + geo + audit patterns.

## Current implementation anchors (what exists today)

- **Approvals**: `ApprovalRequest` already persists per-order approval state with requester/decider metadata and a `pending|approved|rejected` status field.【F:erp/models/core_entities.py†L57-L82】
- **Maintenance**: `MaintenanceTicket` tracks severity, status, assignments, and geo fields (`site_lat`, `site_lng`, `site_label`, `last_geo_heartbeat_at`).【F:erp/models/core_entities.py†L85-L120】
- **Client onboarding shell**: `ClientRegistration` stores pending client signups and basic name/email status, and auth routes queue registrations during signup.【F:erp/models/core_entities.py†L295-L310】【F:erp/routes/auth.py†L139-L148】
- **Admin review UI**: The user management blueprint lists pending client registrations and allows admins to approve/reject them, enforcing `@require_roles("admin")`.【F:erp/user_management/__init__.py†L38-L118】
- **Geo-captured sales activity**: `MarketingVisit` requires `lat`/`lng` per visit, giving a pattern for location-stamped sales/marketing events.【F:erp/marketing/models.py†L14-L29】

## Requirements-to-code gap matrix

| Control point | Current coverage | Gaps vs requirement | Recommended action |
| --- | --- | --- | --- |
| Client onboarding (TIN, institution data, address, approval gating) | Minimal `ClientRegistration` (name, email, status) and admin approval endpoints.【F:erp/models/core_entities.py†L295-L310】【F:erp/user_management/__init__.py†L38-L118】 | No institution/TIN/address fields; no linkage from approval to active client account; no address decomposition; no status history. | Introduce `Institution` entity with TIN + full address; extend registration request fields; approval flow should create `ClientAccount`/institution records and audit decisions. |
| RBAC policy separation (client vs employee vs admin) | `@require_roles` decorators used in admin/user-management and finance routes.【F:erp/user_management/__init__.py†L38-L118】 | Policies are route-scattered; no central policy enforcement point; client role boundaries not explicitly enforced. | Add a centralized authorization helper mapping role-permission sets; enforce on blueprints consistently (deny-by-default). |
| Approval workflows (orders, maintenance, delivery, client registration) | `ApprovalRequest` model exists for orders.【F:erp/models/core_entities.py†L57-L82】 | No generic multi-entity workflow; no supervisor vs admin gating; no timeline/audit trail of state transitions. | Generalize `ApprovalRequest` to handle entity type/id; add status history table and role requirements per request. |
| Sales commission logic | Orders lack initiator/assignment/commission fields.【F:erp/models/order.py†L1-L55】 | No commission accrual/eligibility tracking tied to payment settlement. | Add initiator fields, sales_rep assignment, commission rate/status columns; create `CommissionAccrual` + `CommissionPayout` tables with settlement hooks. |
| Maintenance geo capture & SLA | Maintenance tickets include geo fields but no capture workflow or escalations tied to timestamps.【F:erp/models/core_entities.py†L85-L120】 | No check-in/out events, no SLA timers, no overdue alerts. | Add maintenance event table with geo/time stamps; background SLA watcher that raises approvals/alerts when overdue. |
| Procurement/import ticketing | Not represented in core models reviewed. | Entire lifecycle missing (PI → shipment → customs → receiving). | Add `ProcurementTicket`/`ImportShipment` models with milestones, responsible owner, and approvals. |
| Analytics/reporting & performance | `AnalyticsEvent` stores metric snapshots.【F:erp/models/core_entities.py†L41-L55】 | No unified activity/event stream or scorecards for employees. | Add `ActivityEvent` table; monthly scorecard generation tied to roles/targets. |
| Geo privacy/consent | Marketing consent model exists for marketing/location opt-in.【F:erp/marketing/models.py†L95-L107】 | No explicit consent logging for employee geolocation tracking. | Extend consent/policy to employee geo tracking with purpose and versioning. |

## Migration plan (Alembic-ready additions)

1. **Institution + enriched client registration**
   - `institutions`: `id`, `org_id`, `tin (unique per org)`, `legal_name`, `region`, `zone`, `city`, `subcity_woreda`, `kebele`, `street`, `house_no`, `gps_hint`, `main_phone`, `main_email`, timestamps.
   - Extend `client_registrations`: add institution fields (TIN, legal name), contact person, position, phone, and full address fields; add `decision_notes`.
   - `client_accounts`: add `institution_id` FK; enforce activation only after approval.

2. **Approval workflow generalization**
   - Add `entity_type` (enum) and `entity_id` to `approval_requests`; add `required_role`, `current_state`, `due_at`.
   - New table `approval_events`: `approval_request_id`, `from_state`, `to_state`, `actor_id`, `notes`, timestamp.

3. **Order + commission extensions**
   - Add to `orders`: `initiator_type`, `initiator_id`, `assigned_sales_rep_id`, `commission_rate`, `commission_enabled`, `commission_status`, `payment_status`.
   - New tables `commission_accruals` (per order) and `commission_payouts` (batched per rep per month) with FK to orders and payments.

4. **Maintenance geo & SLA telemetry**
   - New table `maintenance_events`: `ticket_id`, `event_type` (created/check_in/check_out/escalated), `lat`, `lng`, `geo_label`, `notes`, `occurred_at`, `actor_id`.
   - Add `sla_due_at`, `escalation_level` to `maintenance_tickets`; index `status`+`due_at` for overdue queries.

5. **Procurement/import workflow**
   - Tables `procurement_tickets` and `import_shipments` with milestone timestamps (PI issued, LC/TT, departed, arrived port, customs cleared, warehouse received), assigned owner, `status`, `risk_flag`.
   - Add optional linkage to inventory receiving entries.

6. **Activity and consent logging**
   - `activity_events`: actor (user/employee/client), `entity_type`, `entity_id`, `action`, `metadata`, timestamp.
   - Extend `marketing_consents` or new `geo_tracking_consents` for employees with `purpose`, `version`, `accepted_at`, `revoked_at`.

## Workflow/state machine specifications

- **Client registration**: `draft → submitted → pending_review → approved|rejected → account_provisioned`. Approval step creates institution + client account; audit events capture reviewer, decision, notes.
- **Order lifecycle with approval and commission**: `draft → submitted → supervisor_review → approved → invoiced → delivered → payment_settled → commission_eligible → commission_paid`. Client-initiated orders skip commission unless `commission_enabled` is set with an assigned rep.
- **Maintenance**: `open → dispatched → onsite_check_in (geo stamped) → in_progress → resolved → closed`; SLA monitor escalates to `overdue/escalated` when `now > sla_due_at`.
- **Procurement/import**: `ticket_open → sourcing → PI_issued → payment(L C/TT) → production/shipment → customs → warehouse_received → posted_to_inventory → closed`; approvals required at PI issuance and payment.

## Role/permission outline (least-privilege)

- **Client**: submit/view orders, maintenance tickets, complaints; view own delivery/payment status.
- **Sales rep**: create client orders, log marketing visits (geo required), view assigned commissions; cannot approve orders.
- **Engineer**: view/accept maintenance tickets, log onsite geo check-ins, close tasks; no finance access.
- **Tender/procurement officer**: manage procurement/import tickets, upload milestones, request approvals.
- **Junior accountant/cashier**: record payments, update payment status; no role/permission admin.
- **Supervisor/manager**: approve client registrations, orders, maintenance, deliveries; view dashboards; cannot edit security settings.
- **Admin**: full system configuration, role management, and security settings.

## Next steps

1. Create Alembic revisions for the migration plan above (order of operations: institutions → approvals → commissions → maintenance events → procurement → activity/consent).
2. Add centralized authorization helper to register role-permission maps and update blueprints to call it before handlers.
3. Wire UI forms and APIs for enriched client registration and approval actions; reuse existing `ClientRegistration` UI as base.
4. Add SLA/commission workers (Celery/cron) to transition states automatically based on due dates and payment settlement.
