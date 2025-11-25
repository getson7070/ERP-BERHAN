# F20 — Scenario-Based Regression Harness (Business Day Simulator)

This blueprint adds an end-to-end scenario harness to prevent regressions in real-world flows. It layers on top of prior work (F1–F19 and the 21 tasks) without altering existing endpoints or schemas.

## 1) Canonical scenarios to automate first

Start with the most business-critical flows and represent them as end-to-end tests (pytest or scenario scripts):

- **A1 Inventory/Orders:** Create client → Create order → Reserve stock → Confirm payment → Generate invoice → Adjust inventory; assert ledger + balance consistency.
- **A2 Receiving/Allocation:** Receive shipment with batch/expiry → Allocate oldest stock first for new order; ensure no negative stock.
- **B1 Banking/Finance:** Import bank statement → Reconcile unpaid invoices → Update client balances; verify double-entry integrity.
- **C1 Reporting:** End-of-day sales report + inventory reconciliation snapshot; compare to ledger sums.
- **Ops/Bots:** Bot-driven order creation should produce the same results as UI path (idempotent, no dupes).

## 2) Execution modes

- **CI:** Run `pytest tests/scenarios -q` after unit/functional tests; block merges on failure.
- **Scheduled:** Nightly or weekly run against staging-like data to catch drift from config/infra changes.
- **Ad-hoc:** Run before major releases or feature-flag cutovers to validate both legacy and new paths.

## 3) Ties to SLOs and feature flags

- New flagged features (F19) must include at least one scenario covering the new path and the legacy path.
- When an SLO (F18) breach occurs, map it to a scenario; if none exists, add one so the failure cannot recur silently.

## 4) Data and fixtures

- Use existing factories/fixtures; avoid brittle hard-coded IDs.
- Prefer in-memory or transactional DB fixtures to keep runs fast; seed minimal data per scenario.
- For staging runs, sanitise data and reset to known baselines before execution.

## 5) Reporting and ownership

- Publish scenario results in CI artifacts and optionally to a bot/channel for quick visibility.
- Assign owners per scenario family (Inventory, Orders, Reports, Banking, Bots) to keep flows current with business reality.

## 6) Expert challenges and mitigations

- **Coverage gaps:** Start with 5–10 scenarios that reflect revenue-critical flows; expand incrementally after incidents.
- **Flaky tests:** Use deterministic fixtures and isolate external dependencies via stubs/fakes; flakiness should block promotion until fixed.
- **Dual paths rot:** When a feature flag is retired, remove the legacy path and update scenarios to the single source of truth.
