"""Read-only migration checker used in CI/deploy.

- Prints heads and exits non-zero if multiple heads are found.
- Does *not* generate or write new revision files during deploy.

Create merge revisions locally and commit them to the repo.
"""
from __future__ import annotations
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory

def main() -> int:
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = list(script.get_heads())
    print("[check-migrations] heads:", heads)
    if len(heads) != 1:
        print("ERROR: Multiple Alembic heads detected. Merge locally and commit the merge revision.")
        return 2
    from alembic import command
    command.upgrade(cfg, "head")
    print("[check-migrations] upgrade head OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
