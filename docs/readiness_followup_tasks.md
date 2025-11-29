# Production Readiness Follow-up Tasks

The review of code, database utilities, security controls, deployment docs, and tests uncovered these actionable tasks:

1. **Fix typo in deployment snapshot output example**  
   The DB snapshot example in `README-DEPLOY.md` renders the timestamp placeholder as a Python module repr (`<module 'datetime' ...>`) instead of the intended datetime string. Update the example (or the underlying template) to show the actual `yyyyMMdd_HHmmss` timestamp so operators can copy the command without confusion.【F:README-DEPLOY.md†L54-L58】

2. **Stabilize dialect detection when environment changes**  
   The global `_engine` cached in `db.py` is created on first use and never cleared, so later calls to `get_dialect()` ignore updated `DATABASE_URL`/`DATABASE_PATH` values. This makes migrations/tests that swap databases reuse the wrong engine and dialect. Add a reset hook (or avoid caching) so the engine respects environment changes, especially in CI where SQLite fallbacks are expected to stay isolated.【F:db.py†L8-L27】

3. **Align DB snapshot documentation with the script output**  
   `README-DEPLOY.md` claims the snapshot filename expands to the module repr, but `tools/db_snapshot.ps1` actually writes a timestamped file like `snapshots/erp_20250101_120000.sql`. Update the README to match the script’s behavior to prevent operators from searching for a non-existent filename format.【F:README-DEPLOY.md†L54-L58】【F:tools/db_snapshot.ps1†L1-L11】

4. **Harden dialect tests against cached engine leakage**  
   `tests/test_db_dialect.py` mutates `DATABASE_URL`/`DATABASE_PATH` across tests without resetting the global engine, so the first test executed determines all subsequent outcomes. Add a fixture to clear `_engine` (or construct a fresh engine per test) and assert the dialect after both PostgreSQL and SQLite setups to keep the test meaningful and isolated.【F:tests/test_db_dialect.py†L1-L16】【F:db.py†L8-L24】
