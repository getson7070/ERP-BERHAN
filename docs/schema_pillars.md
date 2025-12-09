# ERP-BERHAN Pillar Schema Blueprint

This blueprint captures the six-pillar schema requested for ERP-BERHAN. It provides a normalized, relational design ready for RBAC enforcement, multi-level approvals, automation hooks, and observability. All identifiers use UUIDs, timestamps are in UTC, and foreign keys are indexed for reliable joins.

## 1. Identity & Access Model
- **Tables:** `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `auth_logs`, `user_password_history`, `user_sessions`, `api_keys`
- **Highlights:**
  - Clean RBAC through `user_roles` and `role_permissions` plus audit-friendly `auth_logs`.
  - MFA-ready with `mfa_secret`, `last_login_at`, and device/session fingerprinting via `user_sessions`.
  - Password hygiene enforced with `password_rotated_at`, `must_reset_password`, lockout counters, and `user_password_history` for reuse prevention.
  - API and integration safety through hashed `api_keys` with expirations, rotation metadata, and last-used tracking.
- **Key constraints:** unique `email`, optional unique `phone`, `is_active` default true, cascading deletes from `roles`/`permissions` into join tables, CHECKs to keep lockout counters non-negative, and UNIQUE `(user_id, is_current)` on sessions to simplify active-session validation.

## 2. Client & Onboarding Model
- **Tables:** `clients`, `client_addresses`, `client_approvals`, `client_contacts`, `client_verifications`, `client_onboarding_tasks`, `client_invites`
- **Workflow:** client self-registers with TIN and institution data → admin reviews → verification/KYC checks recorded in `client_verifications` → onboarding tasks tracked in `client_onboarding_tasks` → approvals lock in access via linked `user_id`; reusable invite links handled via `client_invites` with expiry and one-time use flags.
- **Key constraints:** unique `tin`, status enumerated (`pending`, `approved`, `rejected`, `blocked`), `approved_by` references `users`, invites enforce `UNIQUE (client_id, email, is_active)` to prevent duplicate open invitations, and onboarding tasks carry `CHECK` constraints on status progression.

## 3. Employee & Supervisor Model
- **Tables:** `employees`, `positions`, `supervisor_links`, `approval_levels`
- **Workflow:** technician → senior technician → regional manager → admin, with chain enforced via `supervisor_links` and level-aware approvals.
- **Key constraints:** `positions.name` unique, `employees.supervisor_id` references `employees`, cyclical chains blocked with a deferred uniqueness check on `(employee_id, supervisor_id)` plus NOT VALID `CHECK (employee_id <> supervisor_id)` for safety.

## 4. Orders, Approvals, Commission Engine
- **Tables:** `orders`, `order_items`, `order_status_history`, `order_approvals`, `commissions`, `delivery_records`, `pricing_rules`
- **Workflow:** client submits order → employee reviews → supervisor approves → commission computed → delivery scheduled → invoice generated.
- **Key constraints:**
  - `orders.status` constrained to (`draft`, `submitted`, `approved`, `delivered`).
  - `order_items` carry `discount` and `final_amount` for traceable pricing.
  - `commissions` support `flat`, `percent`, and `tier` types with a status lifecycle.

## 5. Maintenance, Geo, SLA & Escalation
- **Tables:** `maintenance_requests`, `maintenance_assignments`, `maintenance_status_history`, `maintenance_sla`, `maintenance_escalations`, `technician_locations`, `geo_events`
- **Workflow:** client reports issue → system/admin assigns technician → SLA timers start → escalate on breach → track technician movement.
- **Key constraints:** SLA deadlines captured via `sla_due_at`; escalations reference both request and assignment to keep lineage; geo events store device and technician context.

## 6. Procurement, Shipping, Customs, Warehouse & Landed Cost
- **Tables:** `purchase_requests`, `purchase_orders`, `proforma_invoices`, `shipments`, `shipping_documents`, `customs_entries`, `warehouse_intake`, `landed_costs`, `suppliers`
- **Workflow:** PR → PO → PI → Shipment → Customs → Warehouse → Landed Cost → Stock Update.
- **Key constraints:** `landed_costs` store granular components (duty, VAT, freight, bank charges, warehouse fees, other costs) with computed `total_landed_cost` and `allocated_cost_per_unit` columns.

## Security & Reliability Guardrails
- All tables include `created_at`/`updated_at` audit timestamps and `CHECK` constraints where appropriate (e.g., positive monetary amounts, non-negative quantities).
- Foreign keys are `ON DELETE RESTRICT` unless otherwise noted to preserve history; join tables cascade deletes to avoid orphans.
- Indexes on foreign keys and high-cardinality search fields (emails, TINs, status history timestamps) ensure predictable query plans.
- The blueprint is compatible with Alembic by running the SQL in `migrations/pillars_schema.sql` or translating it into ORM models; it is tenant-safe when paired with existing `resolve_org_id()` scoping.
