# F7 — Data Integrity & Reconciliation (Inventory · Orders · Finance · Reports)

## Objective
Make it mathematically hard for inventory, orders, finance, and reports to drift, and surface mismatches immediately with auditable remediation paths.

## Canonical Movement Model
- Establish a single `inventory_movements` ledger: `id`, `org_id`, `item_id`, `warehouse_id`, `movement_type`, `quantity_delta`, `ref_table`, `ref_id`, `created_at`, `created_by`.
- Inventory balance = `SUM(quantity_delta)` per `(org_id, item_id, warehouse_id)`; all modules (orders, GRNs, returns, adjustments, transfers) record via this model.
- For legacy paths, add adapters that emit movements without breaking existing documents; migrate gradually to avoid double-counting.

## Invariants & Guard Rails
- `quantity_delta` accumulation may not drive stock < 0 unless `allow_negative_stock` is explicitly enabled per-org.
- Finance: every posting must be balanced or marked `unbalanced` and blocked from final ledger; expose state for audits.
- Orders: enforce `order_total >= invoiced_total >= paid_total`; block or route to approval on violation.
- Enforce invariants in services (not just UI) with unit tests covering negative paths; log violations to incident/audit logs.

## Daily Reconciliation Jobs
- Inventory: recompute balances from movements and compare to cached `inventory_balances`; if drift exceeds threshold, create `reconciliation_issues` + alert via Telegram/email.
- Orders/Finance: flag orders without invoices after X days, invoices without payments after Y days, and orphaned payments; emit daily “top inconsistencies” report per org.
- Reports: sanity-check critical metrics by comparing raw ledger sums vs reporting views; alert on mismatch.

## Drift Dashboard (Admin-Only)
- Panels: negative stock items, large/frequent adjustments, aging orders without invoices, unpaid invoices, reconciliation status (last run timestamp, open issues by severity).
- Wire to RBAC so only senior inventory/finance admins see sensitive data.

## Data Repair Workflow
- `reconciliation_issues` model: `issue_type`, `linked_object`, `proposed_fix`, `status`, `resolution_notes`, `resolved_by`, `resolved_at`.
- UI flow: admins review context, accept proposed fix (create adjustment), manually correct, or dismiss; every resolution writes to audit log and preserves org/tenant boundaries.
- Provide safe scripts/tasks for batch resolution with idempotency and dry-run modes to prevent accidental corruption.

## Rollout & Ownership Questions
- Who owns reconciliation backlogs (inventory lead vs finance lead) and what is the SLA for closing issues?
- How to prevent legacy data double-counting during migration—run reconciliation in shadow mode before enforcing blocks.
- Will the team tolerate short-term friction (more alerts/blocks) to burn down drift, or require a gradual threshold-based rollout?
