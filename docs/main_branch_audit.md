# ERP-BERHAN Main-Branch Production Readiness Audit

## Executive verdict
The main branch is **still not ready for production**, but the import-blocking `bank_connections` collision has been cleared. Application startup now proceeds further, yet the automated test suite fails during stock-service flows because the test database/session harness is unstable and UUID-backed ledger rows are receiving integer primary keys under SQLite. Until the test harness and ledger model alignment are fixed, no release candidate should be cut.

## Current blockers
1. **Test harness instability** – The shared pytest fixtures create database sessions with a manual scoped session and transaction rollback. During app bootstrap the session/connection closes unexpectedly, causing `ResourceClosedError` before tests run. 【F:conftest.py†L18-L76】【719d98†L1-L140】

2. **Stock ledger UUID/id mismatch in SQLite** – `StockLedgerEntry` inserts fail with `AttributeError: 'int' object has no attribute 'hex'`, indicating a UUID column is receiving an integer when running against SQLite. This prevents any stock-engine test from completing and leaves inventory invariants unvalidated. 【719d98†L87-L145】

## Impact
- **Release risk:** No green test signal; inventory and order integrity remain unverified.
- **Data quality:** Ledger inserts fail in tests, implying potential UUID handling issues that could surface in alternative deployments or migrations.
- **Operational readiness:** Without stable fixtures, CI cannot exercise critical modules (inventory/orders/finance), and regressions may ship unnoticed.

## Recommended remediation
1. **Stabilize pytest fixtures:** use Flask-SQLAlchemy’s recommended session/transaction pattern (nested transactions per test) to avoid closed connections under SQLite/Postgres. Verify `Organization` seeding happens within the same live session.
2. **Align ledger IDs with UUID type:** ensure `StockLedgerEntry.id` uses `uuid.uuid4` defaults in tests and production, and avoid SQLite integer autoincrement for UUID columns (explicit GUID type or SQLite adapter).
3. **Re-run core suites:** once fixtures and UUID handling are fixed, rerun `pytest tests/services/test_stock_service.py` and broader suites to regain a green baseline.
4. **Maintain deployment freeze:** do not promote builds until tests pass and the ledger/fixture fixes are validated in staging.

## Direct download
This audit lives at `docs/main_branch_audit.md` in the repository for direct download.
