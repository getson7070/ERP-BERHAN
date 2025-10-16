# ERP-BERHAN Upgrade Pack (v87)

## What changed
- Safer Alembic pre-deploy script (no auto-merge unless AUTO_MERGE_MIGRATIONS=1)
- Robust `migrations/env.py` with DB timeouts and dynamic metadata discovery
- Graph checker (`scripts/migrations/check_migration_graph.py`) to detect duplicate IDs and missing parents
- Templates for creating a no-op shim and merge revisions
- Template coverage checker for `render_template()`
- Security headers module
- CI smoke test for migrations

## One-time steps
1. Commit these files
2. Run `python scripts/migrations/check_migration_graph.py` locally; resolve duplicates/missing parents
3. If DB points to a missing revision, create a shim from template
4. In staging only: set `AUTO_MERGE_MIGRATIONS=1` to merge divergent heads once
5. Deploy → once converged, remove the staging-only env flag
