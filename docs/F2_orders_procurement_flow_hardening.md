# F2 — Orders & Procurement Flow Hardening

This addendum builds on the existing F-series and 21-task roadmap to reduce risk across orders, procurement, inventory, and finance without rewriting earlier work.

## Objectives
- Enforce a canonical order lifecycle and eliminate half-states.
- Tie orders to inventory and finance through explicit links and idempotent operations.
- Guard against race conditions (double approvals, oversells, duplicate webhooks).
- Standardize validations and approvals across APIs, UI, and automation.

## Canonical Order State Machine
- Use a single state progression: `draft → pending_approval → approved → in_fulfillment → partially_fulfilled → fulfilled → closed/cancelled`.
- Keep purchase, sales, and internal transfer orders aligned via shared enums/constants (e.g., `erp.orders.constants`).
- Restrict status changes to a service layer (e.g., `OrderService`); block direct writes from views/tasks.
- Apply SQL CHECK/validation to prevent illegal transitions where feasible.

## Strong Linking Across Domains
- Enforce FKs: order lines ↔ inventory items; orders ↔ client/supplier; orders ↔ financial docs (invoice/credit note).
- Add fulfillment links: order fulfillment records map directly to stock movements; order payments link to bank transactions/vouchers.
- Rule: inventory movements tied to orders must come through fulfillment records—not ad-hoc adjustments.

## Concurrency Safeguards
- Optimistic locking/version checks on order updates; surface reload prompts when conflicts occur.
- Split reservations vs deductions: reserve at approval, deduct on fulfillment (partial or full) to avoid oversells.
- Background jobs touching orders/inventory must be idempotent (unique operation keys like `order:<id>:fulfill`).

## Unified Validation and Guardrails
- Central validator (`validate_order`) checks client/supplier status, price tolerances, stock availability (or negative-stock policy), required fields.
- Reuse validator in API handlers, HTML forms, and Celery workflows for consistent behavior.

## Approval Automation
- `ApprovalRule` (org-scoped) defines thresholds per order type; `OrderApproval` records decisions with actor, time, and comment.
- Approval surfaces: Telegram bot commands/buttons and web UI tabs.
- Idempotent approvals: repeat decisions by the same user must not double-apply.

## Testing Focus
- Unit tests: valid/invalid state transitions; reservation vs fulfillment logic.
- Integration flows: client → order → approval → allocate stock → fulfill → invoice → payment.
- Negative cases: fulfillment beyond availability, bypassed approvals, duplicate webhook/task events.

## Security, UX, and Data Quality Notes
- Apply RBAC consistently to approvals, adjustments, and financial postings; enforce org scoping on all queries.
- Keep UI confirmations and clear error messages for high-risk actions (approvals, adjustments, allocations).
- Ensure schema FKs and constraints remain migration-safe; prefer additive migrations with validation guards.
