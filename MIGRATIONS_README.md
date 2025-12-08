# ERP-BERHAN Migration Guide — v6

- Canonical migration root: `migrations/`. A legacy `alembic/` directory that
  only contains `env.py` is tolerated, but the health check will emit a warning;
  prefer deleting it once local clones no longer depend on the shim.
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

Health endpoints now surface migration warnings (for example, when the legacy
`alembic/` env shim co-exists with `migrations/`). Warnings do not block deploys
but should be cleaned up when convenient.

If you see only a warning like:

```
[migration-check][warning] Detected legacy alembic/ env shim alongside migrations/...
```

you can safely remove the legacy `alembic/` folder (after confirming no local
scripts depend on it) or leave it in place; the check will still return `0`.

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

### Windows / compose workflows (no container writes)

When running on Windows with Docker Desktop, avoid generating merge revisions
**inside** the container because the runtime user (`appuser`) cannot write to
`/app/migrations/versions`. Instead:

1. Activate your local virtualenv and generate the merge on the host:

   ```powershell
   .\.venv\Scripts\activate
   $env:ALEMBIC_INI = "alembic.ini"
   alembic heads
   alembic merge <head1> <head2> -m "merge_heads"
   ```

2. Commit the merge revision so all environments pick it up.

3. Run the preflight check inside an ephemeral container (no DB needed) to
   confirm the tree is clean:

   ```powershell
   docker compose -f docker-compose.migrate.yml run --rm migrate python tools/check_migration_health.py
   ```

This sequence prevents the `PermissionError` seen when trying to run `alembic
merge` inside a container and gives a consistent single-head graph before
booting the stack.

## Rebuilding images

If compose still shows permission issues when generating merge revisions,
rebuild the image without cache so the `/app` ownership change is applied:

```
docker compose build --no-cache web
```
