# Online Alembic Migrations

To avoid downtime when evolving the database schema, run Alembic migrations in
"online" mode:

1. **Create revision**
   ```bash
   alembic revision -m "add new table" --autogenerate
   ```
2. **Verify for backward compatibility**
   - Ensure new columns are nullable or have defaults.
   - Avoid destructive changes; use `CREATE INDEX CONCURRENTLY` where possible.
3. **Run migration**
   ```bash
   ALEMBIC_CONFIG=alembic.ini alembic upgrade head
   ```
4. **Monitor**
   - Track migration status via logs and database metrics.
   - Roll back using `alembic downgrade` if errors occur.

See also `docs/DSAR_RUNBOOK.md` for handling data requests during migrations.
