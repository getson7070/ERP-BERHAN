# Full Pytest Run Report

- **Timestamp:** 2025-11-19 13:43:23 UTC
- **Command:** `ALLOW_INSECURE_DEFAULTS=1 pytest`
- **Environment:** Python 3.12.12, pytest 8.4.2 (per test session banner)

## Result Summary

The full-suite pytest invocation halted during collection with **21 errors** and **10 skipped tests**. No tests executed due to early import and dependency failures.

## Notable Failures

| Category | Details |
| --- | --- |
| Encoding issues | `tests/chaos/__init__.py` cannot be imported because of invalid UTF-8 bytes (0xBF). |
| Missing third-party deps | `bs4`, `boto3`, and `plugins` packages are not installed, causing failures in CSP nonce, storage, and Telegram plugin tests. |
| Broken scripts references | Several tests import from a `scripts` package (`scripts.access_recert_export`, `scripts.update_status`) that is absent from the repository path. |
| Syntax errors | Two selenium/offline worker tests embed Windows PowerShell fragments (`if __name__ -eq "__main__": n`) which are invalid Python syntax. |
| Inventory/RBAC models | UI and traceability tests fail because `erp.db` does not expose `Inventory`, `Lot`, or `UserDashboard` models expected by the tests. |
| Missing imports | `tests/test_rbac_hierarchy.py` raises `NameError: name 'os' is not defined` since the fixture file never imports `os`. |

## Next Steps

1. **Restore/clean UTF-8 encoding** for `tests/chaos/__init__.py` (remove BOM / 0xBF) so pytest can import the chaos test package.
2. **Install required optional dependencies** (e.g., add `beautifulsoup4`, `boto3`) or guard the affected tests with conditionals/marks until the modules exist.
3. **Provide the missing `scripts` package** or refactor the tests and production code to reference available modules for access recertification exports and status updates.
4. **Fix syntax errors** introduced by PowerShell artifacts in `tests/selenium/test_homepage.py` and `tests/test_service_worker_offline.py`.
5. **Export the Inventory/RBAC models** expected by the UI tests or update those tests to point at the correct ORM modules.
6. **Import `os`** within `tests/test_rbac_hierarchy.py` so the fixture runs.

Addressing the above blockers will allow a clean collection phase; additional runtime assertions may surface afterwards.
