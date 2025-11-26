# ERP-BERHAN Main-Branch Production Readiness Audit

## Executive verdict
The main branch is **closer but still not ready for production**. The import-blocking `bank_connections` collision is resolved **and the stock engine now runs cleanly under pytest** (see command output below). We stabilized the test harness and aligned ledger reference handling so UUID-backed inserts no longer crash under SQLite. The remaining freeze should stay in place until the broader suite (orders/finance/bots) is exercised in CI and post-deploy smoke checks are added.

## Current blockers
1. **Test harness stability** – The pytest fixture now binds a dedicated connection per test and rolls back safely. Core stock tests run without `ResourceClosedError`, but the fixture still needs to be exercised across all modules to guarantee isolation at scale. 【F:conftest.py†L18-L73】

2. **Ledger reference/UUID handling** – `StockLedgerEntry.reference_id` now stores string references to avoid SQLite UUID casting errors, and inventory invariant tests seed ledger state to keep balance/ledger sums aligned. Core stock suites are green. 【F:erp/inventory/models.py†L70-L79】【F:tests/inventory/test_stock_engine_invariants.py†L81-L171】【F:tests/services/test_stock_service.py†L1-L168】

## Impact
- **Release risk:** Stock engine tests now pass, but the wider suite (orders/finance/bots) still needs to run before lifting the freeze.
- **Data quality:** Ledger inserts now succeed under SQLite; remaining risk lies in unrun modules.
- **Operational readiness:** CI must be expanded to run the full suite and add post-deploy smoke checks before promotion.

## Recommended remediation
1. **Broaden test coverage:** Run the full pytest suite (orders/finance/bots) on CI using the stabilized fixture; add coverage gates.
2. **Post-deploy validation:** Add staging smoke checks and health probes before any Render/production promotion.
3. **CI gates for freeze:** Keep the freeze until the full suite is green and staging smoke passes; then document the lift criteria here.

## Direct download
This audit lives at `docs/main_branch_audit.md` in the repository for direct download.
