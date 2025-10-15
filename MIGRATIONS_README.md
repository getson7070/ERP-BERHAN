# Migration Hygiene & Render Pre-Deploy (v2)

**What changed in v2**
- `automerge_and_upgrade.py` now captures output, detects real heads from `--verbose` or `branches`, and never relies on exceptions to read Alembic errors.
- On failure it prints `heads`, `branches`, and `history --verbose` so you can see *exact* IDs Render sees.
- CI keeps enforcing a single head and flags duplicate `revision` values.

**Render Predeploy**
```
python -m scripts.migrations.automerge_and_upgrade
```
