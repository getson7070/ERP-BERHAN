# F1.4–F1.6 Inventory Integrity Blueprint (Implementation Checklist)

This update turns the F1 conflict-resolution notes into an explicit, code-ready checklist that can be implemented incrementally without destabilising live flows. It focuses on security (tenant isolation, RBAC), data quality, and operational ownership while keeping rollout phased to avoid user disruption.

## Goals

* Treat stock discrepancies as first-class events with a lifecycle and approval routing.
* Provide explicit override paths instead of ad-hoc fixes while preserving auditability and RBAC.
* Add tests and observability to guard invariants (ledger ↔ balance, non-negative rules, tenant isolation, concurrency safety).
* Roll out protections gradually so users are warned before being blocked.

## 1. InventoryDiscrepancy model (add near CycleCount/CycleCountLine)

Create a dedicated model to log mismatches. Suggested SQLAlchemy fields (UUID primary key, timestamp mixins, `org_id` scoped to enforce tenant isolation):

| Category | Fields |
| --- | --- |
| Identity & context | `id` (UUID, pk), `org_id` (int, indexed), `item_id` (FK `Item.id`), `warehouse_id` (FK `Warehouse.id`), optional `location_id`/`lot_id`/`serial_id`, `cycle_count_id` (FK `CycleCount.id`, nullable), `cycle_count_line_id` (FK `CycleCountLine.id`, nullable) |
| Quantities | `expected_qty` `Numeric(18,4)`, `counted_qty` `Numeric(18,4)`, `variance_qty` computed as `counted_qty - expected_qty` (positive = surplus, negative = shortage) |
| Classification | `discrepancy_type` enum: `COUNT`, `DAMAGE`, `EXPIRY`, `THEFT`, `DATA_ERROR`, `OTHER`; `source` enum: `CYCLE_COUNT`, `AD_HOC`, `IMPORT`, `INTEGRATION`; `source_ref` string for external IDs |
| Workflow | `status` enum: `NEW`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `ADJUSTED`; `severity` enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`; `resolution_notes` text |
| Approvals | `created_by`, `reviewed_by`, `approved_by` (FK `User.id`, nullable), `reviewed_at`, `approved_at` |
| Integration hooks | `adjustment_sle_id` (FK `StockLedgerEntry.id`) linking the ledger entry that fixed the discrepancy |

Indexes to include: `(org_id, status, severity)`, `(org_id, item_id, warehouse_id)`, `(org_id, discrepancy_type, source)`. Ensure migrations keep `Numeric` precision consistent with `StockBalance`/`StockLedgerEntry` to avoid rounding drift.

## 2. Discrepancy creation hooks (wire into real flows)

1. **Cycle counts**: when closing a `CycleCount`, compare each `CycleCountLine.counted_qty` with calculated on-hand; create `InventoryDiscrepancy` for lines where `abs(variance) >= threshold` with `source="CYCLE_COUNT"`, `discrepancy_type="COUNT"`, `status="NEW"`.
2. **Ad-hoc/manual adjustments**: any manual stock edit endpoint must first create a discrepancy (`source="AD_HOC"`) before posting the adjustment via StockService; the resulting ledger entry should populate `adjustment_sle_id`.
3. **Imports/integrations**: during stock imports or external reconciliations, accepted differences should create discrepancies tagged `source="IMPORT"`/`"INTEGRATION"` and capture the external reference.
4. **Invariant failures**: when StockService blocks a move (negative stock/over-reservation), record a discrepancy with `severity` derived from the variance magnitude; block the transaction for hard failures, allow with tagging for soft failures.

Add a helper (e.g., `record_discrepancy(...)`) to encapsulate threshold logic, status defaults, and notification enqueueing (Telegram/email) so every call site stays consistent.

## 3. API & UX (extend `erp/inventory/routes.py`)

Add RBAC-guarded endpoints to manage discrepancies and keep UI flows aligned with approval rules:

* `GET /api/inventory/discrepancies`: filters for `status`, `severity`, `item_id`, `warehouse_id`, date range; enforce org scoping and role checks (inventory manager or above).
* `GET /api/inventory/discrepancies/<id>`: include related `CycleCount`, `StockLedgerEntry`, and timeline of status changes.
* `POST /api/inventory/discrepancies/<id>/review`: transition `NEW → UNDER_REVIEW`, set `reviewed_by/at`, and capture notes.
* `POST /api/inventory/discrepancies/<id>/approve`: RBAC-protected; creates a StockService adjustment, links `adjustment_sle_id`, sets status to `ADJUSTED` or `APPROVED` depending on whether the adjustment is immediate.
* `POST /api/inventory/discrepancies/<id>/reject`: mark false positives with notes.

UI/UX guardrails:

* Keep `StockBalance` read-only in admin panels; surface discrepancy details instead of inline edits.
* On order/ATP screens, warn or block when open HIGH/CRITICAL discrepancies exist for the requested item/warehouse and provide an override-with-approval path.

## 4. Reporting hooks (Orders & Reports)

* Orders: when validating ATP or confirming large orders, check for open HIGH/CRITICAL discrepancies on `(org, warehouse, item)`; block or require override with audit trail.
* Analytics: add a lightweight aggregation/materialized view exposing monthly counts, total absolute variance, and top SKUs/warehouses by discrepancy frequency/size. These metrics should feed dashboards and alerts.

## 5. Testing & safety nets

Add targeted tests under `tests/inventory/` to keep coverage close to real flows:

* **Model/migration tests**: ensure `InventoryDiscrepancy` constraints (required FKs, enums, precision) and migrations apply on fresh DB and realistic snapshots.
* **Flow tests**: cycle count variance above threshold creates discrepancies; manual adjustment attempts without logging a discrepancy fail; approving a discrepancy posts a ledger adjustment and updates status; orders endpoint rejects/warns when critical discrepancies exist.
* **Security tests**: RBAC and tenant isolation—non-manager roles cannot approve/reject; cross-org access is blocked.
* **Concurrency & property-based tests**: keep the earlier concurrency and randomized invariant tests to guard race conditions and numeric drift.

## 6. Observability & retention

* Metrics: `stock_movements_total{type="reservation"}`, `stock_movements_total{result="failed",reason="insufficient_stock"}`, `stock_discrepancies_open_total`, `stock_out_of_sync_items`.
* Structured logs: discrepancy creation (org/item/warehouse, expected vs counted, variance, severity, source), approval events (approver, document links, adjustment ledger ID).
* Retention: archive or summarize discrepancies older than 2–3 years (or align with legal/audit policy); ensure indexes support the hottest queries to avoid table bloat on high-volume SKUs.

## 7. Rollout strategy

1. **Phase 0 – Dark launch**: start recording discrepancies + metrics, no blocking; dashboards limited to admins.
2. **Phase 1 – Soft enforcement**: warn/block obvious invalid moves (e.g., >20% negative swing); UI prompts for override requests; weekly backlog review.
3. **Phase 2 – Hard enforcement**: block core flows (deliveries, invoicing-linked moves, maintenance) when critical discrepancies are open unless explicitly approved via the discrepancy workflow.

## 8. Risk and ownership prompts

Be prepared to answer tough reviewer questions:

1. **Operational overhead**: who owns closing discrepancies weekly, and do they have capacity? Bake ownership into approval routing.
2. **False sense of accuracy**: how often will cycle counts run and how are approvers trained to avoid rubber-stamping?
3. **Performance & volume**: what is the retention/archival plan and have indexes been sized for high-volume SKUs?

Open questions to finalize implementation:

1. Who owns discrepancy resolution (warehouse vs. finance) and at what variance thresholds do approvals escalate?
2. What tolerance bands apply by product category (e.g., ±1 unit for consumables vs. zero-tolerance for critical devices)?
3. What data retention/audit window is required (2–3 years vs. 7-year legal horizon)?

Answering these will calibrate thresholds, RBAC, and storage policies before coding migrations or endpoints.
