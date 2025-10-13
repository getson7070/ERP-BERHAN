# scripts/migrations/automerge_and_upgrade.py
from __future__ import annotations
import sys, datetime, re, os
from pathlib import Path
from alembic.config import Config
from alembic import command

def list_heads(cfg: Config):
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(cfg)
    heads = list(script.get_heads())
    return heads

def create_merge(cfg: Config, heads: list[str]):
    """Create a merge-only revision that merges the provided heads."""
    message = f"automerge {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    command.merge(cfg, heads, message=message)

def main():
    cfg = Config("alembic.ini")
    heads = list_heads(cfg)
    if len(heads) > 1:
        # merge all current branch heads into one
        create_merge(cfg, heads)
    # finally upgrade to the single head
    command.upgrade(cfg, "head")

if __name__ == "__main__":
    sys.exit(main())
