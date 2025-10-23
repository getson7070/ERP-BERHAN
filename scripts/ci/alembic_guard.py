#!/usr/bin/env python3
Fail a CI job if Alembic has multiple heads or if upgrade fails on a fresh DB.
import os, subprocess, sys

def run(cmd, env=None):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=False, env=env)

db_url = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/erp_ci"

# Ensure env var for Alembic
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", db_url)
os.environ.setdefault("DATABASE_URL", db_url)

# 1) Check heads
r = subprocess.run(["alembic", "heads"], capture_output=True, text=True)
print(r.stdout)
heads = [line for line in r.stdout.splitlines() if "(head)" in line]
if len(heads) != 1:
    print(f"ERROR: expected 1 Alembic head, found {len(heads)}", file=sys.stderr)
    sys.exit(2)

# 2) Fresh upgrade
if run(["alembic", "upgrade", "head"]).returncode != 0:
    print("ERROR: upgrade head failed", file=sys.stderr)
    sys.exit(3)

# 3) Try single step downgrade (optional, best-effort)
down = run(["alembic", "downgrade", "-1"])
if down.returncode != 0:
    print("WARN: downgrade -1 failed (non-fatal). Consider adding reversible migrations.", file=sys.stderr)

# 4) Re-upgrade
if run(["alembic", "upgrade", "head"]).returncode != 0:
    print("ERROR: re-upgrade failed", file=sys.stderr)
    sys.exit(4)

print("Alembic checks passed.")
