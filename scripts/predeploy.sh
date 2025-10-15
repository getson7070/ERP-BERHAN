#!/usr/bin/env bash
set -euo pipefail

echo "[predeploy] Checking Alembic heads..."
python - <<'PY'
import os, sys, json
from alembic.config import Config
from alembic.script import ScriptDirectory

cfg = Config("alembic.ini")
script = ScriptDirectory.from_config(cfg)
heads = list(script.get_heads())
print("[predeploy] heads:", heads)
if len(heads) != 1:
    print("ERROR: Your repository has", len(heads), "Alembic heads. Merge them locally and commit before deploy.")
    sys.exit(2)
PY

echo "[predeploy] Upgrading to head..."
python -m alembic upgrade head
