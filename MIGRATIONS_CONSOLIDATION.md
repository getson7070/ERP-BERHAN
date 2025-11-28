# Migrations Consolidation — Read Me First

Generated: 2025-10-28T19:36:02Z

This cleanup removes the duplicate WSL app tree and keeps a single migrations lineage (the root project).
Steps:
1) Keep only this 'erp' package. Do not reintroduce wsl-repo/erp.
2) Ensure Alembic 'script_location' points to the root project's migrations.
3) For existing DB:
   - Default: the Docker entrypoint now auto-runs `python tools/repair_migration_heads.py` (unless `SKIP_AUTO_MIGRATION_REPAIR=1`).
   - Manual: `python tools/repair_migration_heads.py` (auto DB prep, merges any stray heads, stamps missing revisions, upgrades to head)
   - Dry preview without writes: `python tools/repair_migration_heads.py --dry-run`
   - Note: The November 2025 head split is resolved by committed merge revision `d6c63256408b_auto_merge_heads.py`; deployments should no longer generate ad-hoc merge files at runtime.
4) Copy .env.example to .env and set real secrets/URIs.
5) Run: python tools/preflight_check.py
