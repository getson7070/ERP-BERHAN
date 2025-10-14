
# Render pre-deploy Alembic fix (v2)

This version correctly finds your **real** `migrations/` folder from
`scripts/migrations/automerge_and_upgrade.py`, disables duplicate revision IDs
*before* Alembic builds the graph, merges **only actual heads**, and then
runs `alembic upgrade head`.

## Install
Place this file at:
  scripts/migrations/automerge_and_upgrade.py  (overwrite existing)

Keep your Render pre-deploy command:
  python -m scripts.migrations.automerge_and_upgrade

## What it prints
- The chosen migrations directory
- Which duplicate files were disabled (renamed to `.disabled.py`)
- The head revisions before merge
- Whether a merge revision was created
- Confirmation of upgrade to head

## Why this helps
Your logs show duplicate revision IDs like `20251010_seed_test_users_dev`,
`a1b2c3d4e5f7`, `c3d4e5f6g7h`. Alembic chokes when the automerge script tries to
walk/merge revisions with overlaps and non-heads. This patch removes duplicates
and merges only heads, avoiding those overlap errors.
