# F1.4–F1.6 Inventory Integrity Blueprint

This document captures the conflict resolution and rollout blueprint for the inventory hardening effort (F1). It translates the high-level guidance into ERP-BERHAN-ready steps so future code changes remain consistent and auditable.

## Goals

* Treat stock discrepancies as first-class events with lifecycle state.
* Provide explicit override and approval paths instead of ad-hoc fixes.
* Add tests and observability to guard invariants (ledger ↔ balance, non-negative rules, tenant isolation).
* Roll out protections gradually to avoid blocking live operations.

## 1. Stock discrepancy model

Introduce a dedicated record to capture mismatches between expected and observed stock. Candidate model fields:

* `org_id`, `item_id`, `warehouse_id`, optional `location_id`/`lot_id`/`serial_id`
* `snapshot_qty` (counted or computed), `ledger_qty`, `difference = snapshot_qty - ledger_qty`
* `detected_at`, `status` (`open`, `investigating`, `resolved`)
* `resolution_note`, `resolved_by` (nullable FK to user)
* `source` ("reconciliation_job", "blocked_transaction", "manual_report")
* `severity` (informational/soft/hard) to drive escalation policy

Triggers for creating discrepancies:

* Nightly reconciliation detects mismatched balance ↔ ledger sums.
* StockService rejects a movement due to negative stock or over-reservation.
* Soft mismatch tolerance exceeded during inbound/outbound flows.

Behavioral contract:

* **Hard-fail**: log discrepancy, abort movement. Caller surfaces a clear error including discrepancy ID.
* **Soft**: log discrepancy, allow movement but flag it (extra ledger note, metric tag).

## 2. Override workflow and approvals

* Reuse the existing approval pattern (see `ApprovalRequest` models if available) or create a lightweight equivalent tied to `StockDiscrepancy`.
* Policy knobs:
  * Quantity/percentage thresholds that decide whether supervisor vs. controller approval is required.
  * Timeouts and escalation targets (e.g., auto-remind approvers after 24h).
* Flow:
  1. StockService raises an `InventoryConsistencyError` when invariant checks fail.
  2. UI/API catches the error, offers "Open discrepancy & request override".
  3. System creates `StockDiscrepancy` + `ApprovalRequest` (FK link), notifies via Telegram/email bot.
  4. On approval, a cycle-count-style adjustment is posted via StockService, discrepancy marked `resolved`, reason + approver stored.

Guardrails:

* Make `StockBalance` effectively derived data: no direct UI edits, admin inline editing disabled.
* All adjustments must run through StockService (cycle counts, returns, scrap, manual adjustments).

## 3. Integrity checks & observability

* **Reconciliation job** (daily/weekly cron): recompute ledger sums per (org, warehouse, item[, lot/serial]) and compare to `StockBalance`. Create discrepancies for mismatches.
* **Metrics** (Prometheus-friendly):
  * `stock_movements_total{type="reserve"}`; `result="failed", reason="insufficient_stock"` counters
  * `stock_discrepancies_open_total` gauge
  * `stock_out_of_sync_items` gauge from reconciliation job
* **Structured logging**:
  * When discrepancies are created (include org, item, warehouse, snapshot, ledger, diff, severity)
  * When overrides are approved (include approver, reason, doc links)

## 4. Testing strategy

Short-term additions that can be implemented without refactoring live flows:

* **Concurrency test** (`tests/inventory/test_stock_concurrency.py`): two DB sessions reserve the last unit; assert only one succeeds, no negative balances, ledger matches balance. Use explicit transactions and `SELECT ... FOR UPDATE` to exercise locking.
* **Property-based invariant test** (`tests/inventory/test_stock_invariants_randomized.py`): generate random sequences of inbound/outbound/reserve/unreserve movements against a clean org/item/warehouse; after each step assert `qty_on_hand` and `qty_reserved` are non-negative, `qty_reserved <= qty_on_hand`, and balance equals cumulative ledger deltas.
* **Org-scope red team test**: ensure all inventory queries filter by `org_id`; attempt cross-org read should return zero rows or raise.

Note: the existing `tests/inventory/test_stock_engine_invariants.py` covers baseline invariants; these additions focus on race conditions and fuzzed sequences.

## 5. Rollout plan

* **Phase 0 (dark mode)**: enable discrepancy creation + metrics without blocking flows. Measure discrepancy volume by org/warehouse/item.
* **Phase 1 (soft-fail)**: block obviously invalid moves (e.g., >20% negative swing, large over-reservations). UI shows warning and prompts for override request.
* **Phase 2 (hard-fail)**: enforce invariants on core flows (deliveries, invoicing-linked movements, maintenance spare parts). Only bypass via discrepancy + approval.

## 6. Open questions to answer before implementing

1. Which modules currently initiate stock movements (sales orders/deliveries, maintenance, internal transfers, samples/FOC)? Prioritize routing those through StockService.
2. Who owns discrepancy resolution operationally (warehouse lead vs. finance controller)? Embed into approval routing.
3. What error tolerance is acceptable in practice (± units or ±%) to avoid blocking legitimate operations during rollout?

## Next steps (actionable stubs)

1. Define `StockDiscrepancy` SQLAlchemy model + migration; wire creation into StockService error paths.
2. Implement reconciliation job (Celery/cron) that logs discrepancies and emits metrics.
3. Add concurrency and property-based tests outlined above; ensure they run with current test fixtures.
4. Add admin/UI protections to prevent direct `StockBalance` edits; surface discrepancy detail and approval flows.

This blueprint keeps F1 focused on integrity and safety while avoiding abrupt runtime changes. Follow-up tasks should implement these steps incrementally and add monitoring to prove correctness in production.
