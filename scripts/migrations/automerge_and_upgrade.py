from __future__ import annotations

import sys
from alembic.config import Config
from alembic import command

def main():
    cfg = Config("alembic.ini")  # assumes repo root execution
    # Just upgrade to head using the clean versions dir set in env.py
    command.upgrade(cfg, "head")
    print("[migrations] upgrade to head completed")

if __name__ == "__main__":
    sys.exit(main())
