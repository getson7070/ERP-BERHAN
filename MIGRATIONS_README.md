# ERP-BERHAN Updates Only — v4

- Fixes syntax error in `scripts/migrations/automerge_and_upgrade.py`.
- Normalizes duplicate Alembic `revision` IDs.
- Auto-writes a merge revision when multiple heads exist, then upgrades to `head`.
- Adds CI guard so you never ship with >1 head again.
- Adds base layout + placeholders for **all 37 missing templates** discovered.

**Apply**: unzip at repo root, commit, ensure Render pre-deploy runs:
```
python -m scripts.migrations.automerge_and_upgrade
```

**New guard (November 2025):** run `python tools/check_migration_health.py` in CI or before any deploy to confirm we only have
a single migration root (`migrations/`) and no multi-head Alembic state.
