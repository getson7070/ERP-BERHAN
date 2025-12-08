# ERP-BERHAN Migration Guide — v5

- Single canonical migration root: `migrations/` (no more `alembic/`).
- Strict multi-head detection via `tools/check_migration_health.py` and
  `init_db._assert_single_migration_head()`.
- Latest merge revision: **20251212100000_merge_commission_and_trade_heads**.
- Base Docker image `chown`s `/app` to `appuser` so Alembic can write revisions
  during `docker compose run web ...` without permission errors.

## How to verify the tree

Run the lightweight guard locally or in CI:

```
python tools/check_migration_health.py
```

Expected output:
`[migration-check] OK: single migration root, correct script_location, single head.`

If the check reports multiple heads, list them explicitly with:

```
alembic heads
```

Then merge them (or apply the latest merge revision) and rerun the check:

```
alembic merge -m "merge_heads" <head1> <head2> [...]
# or rely on the shared merge revision
alembic upgrade 20251212100000
```

## Rebuilding images

If compose still shows permission issues when generating merge revisions,
rebuild the image without cache so the `/app` ownership change is applied:

```
docker compose build --no-cache web
```
