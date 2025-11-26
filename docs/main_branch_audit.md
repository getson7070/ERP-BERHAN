# ERP-BERHAN Main-Branch Production Readiness Audit

## Executive verdict
The main branch is **not ready for production**. Application import fails due to a duplicated `bank_connections` table declaration, which blocks server startup, worker startup, and the test suite. No green test signal exists to validate inventory/order invariants, so deploying would ship an unverified build.

## Blocking issues
1. **Banking model defines the same table multiple times**  
   `BankConnection` repeats the `created_at`/`created_by_id` columns three times. SQLAlchemy registers the `bank_connections` table multiple times in metadata and aborts application startup with `InvalidRequestError: Table 'bank_connections' is already defined for this MetaData instance`. This halts any code path that imports `erp/__init__.py`, including web, workers, CLI, and pytest. 【F:erp/banking/models.py†L59-L85】【f31347†L1-L33】

2. **Test suite cannot run**  
   Because of the banking metadata collision, even targeted tests (e.g., inventory service invariants) fail during app initialization. CI currently lacks a passing baseline, so no invariants or regression coverage can be trusted until the schema issue is fixed. 【f31347†L1-L33】

## Impact
- **Release risk:** Any deployment would crash on import, meaning no production service would come up.
- **Data integrity:** Banking, finance, and any features importing the banking models cannot function; migrations risk diverging from the broken model.
- **Quality gates absent:** With pytest blocked, inventory/order/finance safeguards remain unverified.
- **UX/DB standards unvalidated:** Because the backend cannot boot, no UI/UX or database-quality review can be executed against a running system.

## Recommended remediation
1. **Deduplicate `BankConnection` columns** so each field is defined once and the table is registered a single time. Add `__table_args__ = {"extend_existing": True}` only if absolutely necessary for legacy imports.
2. **Add a smoke test** that imports `erp.banking.models.BankConnection` to guard against future double-registration.
3. **Re-run core suites** once the model is fixed: `pytest tests/services/test_stock_service.py` and the broader suite to re-establish a green baseline.
4. **Gate deployment** until a full green test run is available and UI/UX checks can be executed against a running instance.

## Direct download
This audit lives at `docs/main_branch_audit.md` in the repository for direct download.
# ERP-BERHAN Main Branch Audit (Summary)

## Overview
This audit captures the current health of the `work` branch (tracking main) with a focus on stability, security, and data integrity. Findings are drawn from code inspection and targeted checks executed during this review.

## Critical Findings
1. **Banking models define duplicate columns and trigger metadata collisions**
   - `BankConnection` declares the `created_at` / `created_by_id` pair three times. SQLAlchemy attempts to register the same column names repeatedly, causing the `bank_connections` table to be defined multiple times in the metadata and breaking application startup and tests. This blocks any DB-bound workflow, including pytest startup. 【F:erp/banking/models.py†L59-L86】

2. **Test suite currently fails to boot the app due to the banking table collision**
   - Running even a single test (e.g., `tests/services/test_stock_service.py`) fails during app initialization with `InvalidRequestError: Table 'bank_connections' is already defined for this MetaData instance`. This prevents CI from validating changes and leaves inventory/stock safeguards unverified. 【a475fe†L1-L33】

## Risk and Impact
- **Runtime reliability:** Any code path importing the banking models will raise at import time, effectively bricking the web app, Celery workers, and CLI utilities that load `erp/__init__.py`.
- **Data integrity and migrations:** Duplicate column declarations risk generating inconsistent schema expectations versus existing migrations. Downstream modules (orders, finance, reporting) that rely on bank connections cannot operate or be tested until the model is corrected.

## Recommended Remediation (Safe, Minimal Changes)
1. **Deduplicate the `BankConnection` column definitions**
   - Remove the redundant `created_at` / `created_by_id` pairs so each column is declared once. This should clear the metadata collision and align the model with the migration history.
2. **Add a regression test to guard against table redefinition**
   - A simple import test (e.g., `pytest -q tests/banking/test_models_import.py`) that just imports `erp.banking.models.BankConnection` will catch future reintroductions of duplicate columns or conflicting table args.
3. **Rerun the existing inventory/service tests after the fix**
   - Once the model is cleaned, rerun `pytest tests/services/test_stock_service.py` to verify inventory invariants can execute. Expand to the broader suite as environment allows.

## Observability and Safety Notes
- Keep bank-related tests in the default CI matrix so schema regressions surface immediately.
- Ensure migrations remain in sync with the corrected model; if historical data exists, add an Alembic check to confirm the table shape before deployment.

## Direct Download
This report is available at `docs/main_branch_audit.md` within the repository for direct download.
