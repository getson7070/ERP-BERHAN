# Migration Hygiene & Render Pre-Deploy

## What this bundle contains
- `scripts/migrations/automerge_and_upgrade.py`: robust pre-deploy that detects true Alembic heads and merges them safely, then upgrades.
- `.github/workflows/alembic-one-head.yml`: CI guard that fails if the repo has more than one head or duplicate revision IDs.
- `scripts/migrations/print_heads.py`: quick diagnostic to see heads on the runner.
- `tools/dedupe_alembic.py`: lists duplicate revision IDs across files.

## How to wire it in Render
In `render.yaml` (or the Render dashboard), set **Predeploy Command** to:
```bash
python -m scripts.migrations.automerge_and_upgrade
```

## Local sanity checks
```bash
pip install -r requirements.txt
alembic -c alembic.ini heads -q
python tools/dedupe_alembic.py --check-only
python -m scripts.migrations.automerge_and_upgrade
```

## Clean up duplicates (after deploy is green)
1. Run `python tools/dedupe_alembic.py` to list duplicates.
2. For each duplicate `revision = '...'` shown:
   - Keep the correct file.
   - Rename the extra file(s) to a **new** unique `revision` value and adjust their filenames accordingly,
     or remove them if truly unused.
   - If those files are needed, chain them linearly by setting their `down_revision` to the previous revision
     or create an explicit **merge** revision with `down_revisions = ('revA', 'revB', ...)`.
3. Ensure `alembic -c alembic.ini heads -q` prints exactly one id.
