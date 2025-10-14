from __future__ import annotations
import sys, datetime
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory

def main():
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = list(script.get_heads())
    if len(heads) > 1:
    command.merge(cfg, heads, message="automerge ...")
    command.upgrade(cfg, "head")

if __name__ == "__main__":
    sys.exit(main())
