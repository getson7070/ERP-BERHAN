# F2 – Orders ↔ Inventory Handshake Blueprint

This document translates the F2 plan into an implementation-ready checklist. It complements the F1 discrepancy spine and keeps changes additive so existing flows remain stable while Orders gains consistent inventory validation, auditing, and RBAC-controlled overrides.

## Objectives
- Provide one canonical source for “available to promise” (ATP) that includes stock, reservations, quarantines, safety buffers, and open discrepancies.
- Enforce order invariants and approvals without rewriting existing order models.
- Capture audit data for oversell attempts and overrides to feed reporting and accountability.

## Core Components

### 1) Canonical availability calculator
Implement a single function, e.g. `erp/inventory/services.py:get_available_qty(org_id, item_id, warehouse_id)`, that every order flow must use.

Inputs and behaviour:
- Read **on-hand** from the authoritative stock source (ledger or StockBalance).
- Subtract **committed quantities** from open orders (pending/approved but unfulfilled lines).
- Subtract **quarantined/blocked** stock (damaged, QA hold, returns quarantine) so it is not promiseable.
- Apply **per-item/warehouse safety buffers** (configurable; default 0).
- If open **InventoryDiscrepancy** rows exist for the item/warehouse with status in `NEW/UNDER_REVIEW` and severity `HIGH/CRITICAL`, adjust availability according to policy:
  - Hard lock: set availability to 0.
  - Soft lock: reduce availability or mark the order as requiring override.
  - Monitor-only: do not change quantity but emit warning/log.
- Return a Decimal for precision and reuse across APIs and background jobs.

### 2) Order invariants and validation service
Create a lightweight validator in `erp/orders/services.py` (or equivalent) with a dedicated `OrderValidationError` exception.

Rules to enforce per order line:
- `requested_qty <= available_qty_at_decision_time` (create/approve).
- `fulfilled_qty <= requested_qty` for partial shipments or backorders.
- On cancel: release committed/reserved stock back to availability.
- On shipment creation: create a stock ledger/reservation movement linked to the order/shipment ID.

Use a helper `validate_order_line(line, available_qty)` so API/routes do not perform ad-hoc comparisons.

### 3) API hooks without rewrites
Integrate validation into existing endpoints (e.g. `erp/orders/routes.py`) while keeping model shapes intact:
- **Create order (POST /api/orders):** call `get_available_qty` for each line; on failure return 400/422 or mark order `PENDING_APPROVAL` with `requires_inventory_override=True` depending on per-org config `ALLOW_INVENTORY_OVERSELL`.
- **Update order (PUT /api/orders/<id>):** when line quantity increases or items are added, re-run validation on the delta or new total; when decreased, release commitments.
- **Approve order:** re-check availability to catch races since creation; fail cleanly if stock disappeared.

### 4) Discrepancy integration (ties to F1)
When `get_available_qty` detects open critical discrepancies:
- Hard lock → treat availability as 0 and block unless override allowed.
- Soft lock → mark order as needing discrepancy acknowledgment/approval with recorded reason.
- Monitor → log warning but allow.
Use a centralized query against `InventoryDiscrepancy` scoped by `org_id`, `item_id`, and `warehouse_id`.

### 5) RBAC and approval policy
Align with Task 17 RBAC roles:
- `ROLE_SALES`: create orders but cannot override stock/discrepancy warnings.
- `ROLE_INVENTORY_MANAGER`: may override within configured variance/monetary thresholds.
- `ROLE_FINANCE_MANAGER`: required for high-value overrides.
Endpoint enforcement:
- Create order: `ROLE_SALES` or higher.
- Override/approve with stock shortfall or critical discrepancy: manager/finance only.

### 6) Audit trail and reporting
Record structured events for:
- Order blocked due to insufficient stock or critical discrepancy (include available snapshot).
- Overrides: approver, timestamp, reason, items/lines affected, availability snapshot.
Expose reporting hooks/dashboards:
- Top items by oversell attempts.
- Users with most overrides.
- Orders approved while discrepancies were open.

### 7) Testing coverage (add to `tests/orders/test_inventory_handshake.py`)
- **Happy path:** sufficient stock → order creation/approval succeeds; reservations/ledger updated.
- **Insufficient stock:** normal user receives validation error; no order/reservation created.
- **Approval race:** two orders compete; first consumes stock, second fails on approval due to refreshed availability.
- **Discrepancy interaction:** mark CRITICAL discrepancy → hard lock blocks; soft lock allows with override and audit entry.
- **RBAC:** sales cannot override; inventory manager can within threshold; finance required above monetary limit.

### 8) Performance and concurrency considerations
- Use row-level locks or optimistic versioning on reservation/stock tables when confirming orders to avoid double-commit.
- Consider cached/precomputed availability snapshots if peak order volume makes per-line SUM queries too slow; invalidate on stock/reservation changes.
- Keep queries org-scoped and indexed (`org_id, item_id, warehouse_id` on reservations/stock/discrepancies`).

### 9) Configuration knobs
- `ALLOW_INVENTORY_OVERSELL` (per-org): block vs allow with override.
- Safety buffer percentages/quantities per item/warehouse.
- Discrepancy lock policy: hard/soft/monitor.
- Monetary/variance thresholds mapping to required approver role.

### 10) Rollout plan (minimal disruption)
- **Phase 0 – Dark mode:** compute availability and log/flag violations without blocking; show dashboards to admins only.
- **Phase 1 – Soft enforcement:** warn on critical discrepancies or shortfalls; allow manager override; audit every bypass.
- **Phase 2 – Hard enforcement:** block high-risk flows unless approved; align with training and KPIs.

## Open questions to finalize implementation
- Should orders be hard-blocked on stock issues, or always allow override with audit? (policy per org?)
- Expected peak orders/minute during busy periods (dictates need for caching/denormalization).
- Which department owns consequences of overrides that lead to stock-outs (Sales vs Inventory vs Finance)?

Answering these guides threshold defaults, RBAC mappings, and database/index sizing before coding.
