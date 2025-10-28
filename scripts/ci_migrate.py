from erp.security_hardening import safe_run, safe_call, safe_popen

Utility to exercise Alembic migrations upgrade→head and downgrade→base
using an ephemeral database (default: SQLite file).
Fails CI if migrations are irreversible or multiple heads exist.

import os, sys, subprocess

DB_URI = os.environ.get("DATABASE_URI", "sqlite:///./ci_migrate.db")

def run(cmd):
    print("+", " ".join(cmd), flush=True)
    res = safe_run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(res.stdout)
    if res.returncode != 0:
        sys.exit(res.returncode)

if __name__ == "__main__":
    # Ensure Alembic is available
    if not os.path.exists("alembic.ini"):
        print("alembic.ini not found at repo root; skipping with failure to prevent false green.")
        sys.exit(1)
    # Print current heads to detect multi-head
    run(["alembic", "heads"])
    # Upgrade to head
    run(["alembic", "upgrade", "head"])
    # Downgrade back to base (will fail if not reversible)
    run(["alembic", "downgrade", "base"])
    print("Alembic dry-run completed successfully.")

