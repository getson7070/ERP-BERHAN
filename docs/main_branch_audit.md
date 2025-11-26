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
