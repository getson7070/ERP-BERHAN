# Database Maintenance

## Backup & Restore

The `backup.py` helper creates timestamped backups of the active database. For
PostgreSQL and MySQL connections, it invokes `pg_dump` or `mysqldump` to produce
SQL files that can be shipped off-site for disaster recovery. Example:

```bash
python backup.py postgresql://user:pass@host:5432/erp
```

Backups are written to the `backups/` directory. Store database credentials in
environment variables rather than committing them to source control. Restores
for SQLite databases are supported via:

```bash
python -c "from backup import restore_backup; restore_backup('sqlite:///erp.db', 'backups/<file>.sqlite')"
```

When using PostgreSQL, apply dumps with `psql`:

```bash
psql $DATABASE_URL -f backups/<file>.sql
```

## Connection Pooling

`db.py` configures SQLAlchemy connection pooling to protect the database from
exhaustion under load while reusing existing connections for performance. Tune
pool settings with the following environment variables:

- `DB_POOL_SIZE` – number of persistent connections (default `5`)
- `DB_MAX_OVERFLOW` – additional connections allowed above the pool size (default `10`)
- `DB_POOL_TIMEOUT` – seconds to wait for a connection before raising an error (default `30`)

These settings work alongside Phase 1 security controls such as HTTPS and
row‑level policies. Adjust values based on your expected concurrency and ensure
changes are accompanied by load testing.

### PgBouncer

For large deployments, place [PgBouncer](https://www.pgbouncer.org/) in front of
PostgreSQL and enable *transaction* pooling. Example configuration:

```
[databases]
erp = host=postgres port=5432 dbname=erp

[pgbouncer]
max_client_conn = 100
default_pool_size = 20
pool_mode = transaction
```

Set environment variable `DATABASE_URL` to the PgBouncer service and tune
`DB_POOL_SIZE`/`DB_MAX_OVERFLOW` for application workers. Monitor PgBouncer
statistics to watch for saturation and adjust limits before hitting caps.

## Performance Benchmarks

Use `scripts/benchmark.py` to issue concurrent requests against a deployed
instance and measure throughput. Results help validate tuning and autoscaling
configurations.
