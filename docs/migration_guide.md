# Migration Guide

This guide outlines steps to migrate database schema when new modules are introduced.

1. Ensure backups are taken before applying migrations.
2. Run `alembic upgrade head` to apply latest changes.
3. Verify new tables contain `org_id` and appropriate indexes.
4. Test row-level security policies using multiple tenant sessions.

## Rollback Procedure

If a migration fails:
1. Run `alembic downgrade -1` to revert the last migration.
2. Restore the pre-migration backup if data corruption is suspected.
3. Investigate errors and apply a fixed migration before re-running `upgrade`.

## Data Migration

When schema changes require data transformation:
1. Write idempotent scripts under `scripts/`.
2. Execute scripts after structural migrations and verify row counts.
3. Log actions in `audit_logs` for traceability.
