# ERP-BERHAN Audit (main branch)

## Overview
This audit highlights code health risks observed in the current main branch across migrations, deployment configs, and automated tests. Findings are organized by category with direct pointers to the affected files.

## Duplicate/parallel configuration & migration risks
- **Legacy duplicate migration lineage**: `MIGRATIONS_CONSOLIDATION.md` notes the repo previously contained multiple app trees and instructs keeping only the root `erp` package, implying risk of diverging migration histories. 【F:MIGRATIONS_CONSOLIDATION.md†L1-L11】
- **Multiple Alembic heads unresolved**: `MIGRATIONS_TODO.txt` still directs engineers to merge multiple Alembic heads before upgrading, indicating outstanding migration consolidation work. 【F:MIGRATIONS_TODO.txt†L1-L5】

## Deployment configuration concerns
- **Conflicting compose stacks**: Several docker-compose variants (`docker-compose.yml`, `.min`, `.migrate`, `.prod`, `.override._fix`, `.bak.*`) coexist without documentation tying them together, increasing drift risk between environments. 【F:README-DEPLOY.md†L1-L31】【F:docker-compose.yml†L1-L20】

## Broken and truncated tests/code
- **Corrupted test bootstrap lines**: Both Selenium and offline service worker tests contain malformed `if __name__ -eq "__main__":` lines with injected ``r``n` sequences, preventing module import. 【F:tests/selenium/test_homepage.py†L21-L50】【F:tests/test_service_worker_offline.py†L16-L35】
- **Missing or misnamed domain models**: Inventory tests expect `SerialNumber` and `Lot` exports that are absent from `erp.inventory`, causing import failures. 【F:tests/inventory/test_stock_engine_invariants.py†L9-L18】【F:tests/test_traceability.py†L4-L8】
- **Modules referenced but not present**: Tests reference `scripts` and `plugins.telegram_bot`, which are missing from the codebase, resulting in `ModuleNotFoundError`. 【F:tests/test_retention.py†L4-L10】【F:tests/test_telegram_plugin.py†L1-L6】
- **Optional dependency gaps**: Test suite requires packages like `bs4`, `boto3`, and Playwright drivers that are not installed in the default environment, leading to immediate collection errors. 【813b22†L32-L74】
- **Unicode corruption**: `tests/chaos/__init__.py` fails to decode due to a leading invalid byte, stopping test collection in the chaos suite. 【813b22†L11-L28】

## Test execution status
Running `pytest -q` hits 23 collection errors (encoding issues, missing modules, malformed syntax, and absent dependencies), leaving the suite unusable in its current state. 【813b22†L32-L121】

## Recommended next steps
1. Normalize migration history: remove stale migration roots, merge heads per `MIGRATIONS_TODO.txt`, and document the authoritative Alembic path. 
2. Rationalize deployment configs: consolidate docker-compose variants and ensure README aligns with the supported stack. 
3. Repair corrupted tests: fix the malformed `__main__` guards, replace `r`n artifacts, and restore missing models/modules (`SerialNumber`, `Lot`, `scripts`, `plugins`). 
4. Pin required test dependencies (bs4, boto3, selenium/playwright drivers) or mark tests to skip when unavailable. 
5. Validate chaos suite encoding and re-encode files to UTF-8.
