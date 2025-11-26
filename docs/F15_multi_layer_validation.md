# F15 — Multi-Layer Validation Framework

## Objectives
Make ERP-BERHAN continuously validate critical data paths so inventory, orders, finance, reporting, and automation stay consistent and predictable. This layer is additive to F1–F14 and the original 21 upgrades.

## Components

### 1) Model-Level Validation (per-domain validators)
- Add `erp/validators/` modules (e.g., `inventory.py`, `orders.py`, `finance.py`, `users.py`, `bots.py`).
- Enforce range/format checks, referential sanity beyond FK, and domain rules (e.g., positive quantities, distinct source/target locations, valid status transitions).
- Hook validators into service layers and pre-commit transaction guards rather than view/UI code.

### 2) Cross-Module Consistency Engine
- Scheduled/on-demand engine checks invariants across domains:
  - Inventory ↔ Orders: fulfilled orders must deduct stock; cancellations must restore; no negative on-hand; lots not expired before fulfillment.
  - Finance ↔ Orders: invoices align to orders; payments align to invoices; double-entry balance intact.
  - CRM ↔ Orders: every order references a valid client; no orphan clients with transactions.
  - Bots: no duplicate Telegram messages by `message_id`; no jobs stuck in `processing` beyond threshold.
- Runs via Celery beat, CI pre-deploy sweep, and admin-triggered mode; logs incidents to reconciliation/health tables.

### 3) Predictive Rule Engine (lightweight, no-ML)
- Store rules in DB (per-org optional) fed by analytics/health signals (F8/F9).
- Detect early risk: stock-out forecasts, late deliveries, sales inactivity, churn risk, bot backlog, DB load spikes.
- Emit warnings to UI/bot/notifications; never bypass core invariants.

### 4) Schema Drift Detector
- Tool: `tools/check_schema_drift.py` compares live DB schema vs Alembic metadata; flags missing columns, unused indexes, orphan tables, mismatched defaults.
- Run in CI (blocking for major drift), and optionally in nightly ops report.

### 5) Pre-Commit Transaction Guard
- Wrap critical writes (Inventory/Orders/Invoices) with a guard that runs validators + consistency rules before commit.
- On failure: rollback, log reason, alert admins/bots when severity high.
- Inline checks stay fast; deep checks can defer to async tasks.

### 6) Predictive Breakpoint Simulation (dry-run mode)
- Endpoint/query flag (e.g., `?simulate=true`) runs full validation and rule checks without committing.
- Returns projected effects (stock deltas, reservations, finance impacts, warnings) to help operators during peak periods.

### 7) UI-Level Consistency Warnings
- Surface deterministic warnings for risky actions (negative stock, large payments, price overrides, shipment cancellations, deleting linked clients, assigning to disabled users).
- Warnings reference validator output and require explicit confirmation/override (with audit logging and RBAC checks).

### 8) Automated Daily Consistency Report
- Bot/email report summarizing drift and risks:
  - Orders without stock movements; invoices without payments; expired lots in active stock; stuck bot jobs; reconciliation errors; schema drift result; risk score.
- Sent to admin/ops channels; stored for audit.

## Operational Guidance
- Separate immediate (fast) vs deep (async) validation to avoid latency spikes.
- Provide feature flags for new checks to allow gradual rollout per org.
- Treat legacy data carefully—run in “report-only” mode first, then enforce once noise is reduced.
- Assign ownership for resolving surfaced issues (inventory lead, finance lead, ops lead) to avoid alert fatigue.

## Open Questions for Stakeholders
1. Should blocking validation be applied globally or start as warn-only per org/product?
2. Which operations need simulation mode first (e.g., large orders, bulk adjustments, bank postings)?
3. What latency budget is acceptable for inline guards (<20 ms suggested) before deferring to async checks?
