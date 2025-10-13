
"""
Repairs Alembic multiple-head situations by creating a merge revision.
Usage:
    python tools/repair_migration_heads.py
"""
from alembic.config import Config
from alembic import command
import os, sys

def main():
    cfg_path = os.environ.get("ALEMBIC_INI", "alembic.ini")
    if not os.path.exists(cfg_path):
        print("alembic.ini not found. Run from project root or set ALEMBIC_INI.")
        sys.exit(1)
    cfg = Config(cfg_path)
    # Show current heads
    command.current(cfg, verbose=True)
    # Merge all heads into one
    command.merge(cfg, message="auto-merge heads", branch_label=None, revisions="heads")
    print("Created merge revision. Now run: alembic upgrade head")

if __name__ == "__main__":
    main()
