# Layer 6 — Procurement & Import Tracking (Current Main Branch Audit)

This document captures the current state of the procurement/import features based on the live repository under `/workspace/ERP-BERHAN`, focusing on models, routes, templates, and migrations.

## Scope and Sources Reviewed
- `erp/procurement/models.py`
- `erp/procurement/routes.py`
- `erp/routes/procurement/` (not present)
- `erp/routes/inventory.py`
- `erp/models/core_entities.py`
- `erp/models/order.py`
- `templates/procurement/` (UI forms and lists)
- Alembic migrations under `migrations/versions/` for procurement fields

## Current Implementation
- **Models**: Basic purchase-order model with vendor, amount, status, timestamps. No dedicated line-item table or import-compliance metadata.
- **Routes**: CRUD-style endpoints for procurement records; no staged workflow (draft → PI → shipment → clearance → GRN).
- **Templates**: Simple listing and edit/create forms; no shipment timeline, customs fields, or cost breakdown UI.
- **Integrations**: No linkage to inventory intake, finance/LC, EFDA compliance, or telegram notifications.

## Gaps Against Requirements
- **Trade & Compliance Data**: Missing PI number/date, AWB, HS code, EFDA permit, bank reference, commercial invoice, country of origin, freight/insurance/FOB-CIF terms, customs valuation/duty %, valuation dispute notes, arrival/clearance/warehouse dates.
- **Workflow & Approvals**: No multi-step approval chain (procurement manager/finance/admin), no milestone progression (PI requested/received, bank submitted/approved, shipped, customs, delivered), no SLA timers or escalation.
- **Inventory & Finance Integration**: No goods-receipt/GRN, no landed-cost calculation, no link to LC/TT payments or bank statements, no automatic stock intake by batch/expiry.
- **Line Items**: No `ProcurementItem` table for multi-line POs; no quantity/price/discount/currency handling.
- **Notifications & Auditability**: No telegram/email alerts for milestone changes, no audit log of approvals or document uploads.
- **UI/UX**: Lacks shipment timeline, compliance badges, trade-field inputs, or dashboards for in-flight imports and overdue clearances.

## Risks
- Inability to track import compliance (EFDA/customs) and shipment milestones.
- No separation of duties or approvals for high-value imports → fraud/operational risk.
- No landed-cost or inventory intake linkage → financial reporting inaccuracy.
- Missing audit trail and notifications → poor operational visibility.

## Recommendations (next steps)
1. **Modeling**: Add trade/compliance fields and a `ProcurementItem` table; introduce `ShipmentMilestone` with geo/SLA fields and audit stamps.
2. **Workflow**: Implement a staged state machine with approvals (procurement manager → finance → admin) and SLA timers for PI, bank, shipment, and clearance steps.
3. **Integrations**: Hook GRN to inventory with batch/expiry and landed-cost; add finance linkage for LC/TT records and reconciliation.
4. **Notifications & Audit**: Telegram/email alerts on milestone transitions; persistent audit log of approvals and document uploads.
5. **UI/UX**: Build responsive dashboards for shipments, customs status, and overdue items; forms for PI/AWB/HS code/EFDA/bank data; timeline view with milestone badges.
