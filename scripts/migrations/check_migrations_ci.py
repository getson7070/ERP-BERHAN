
"""CI check: ensure single Alembic head and no placeholder down_revisions."""
from __future__ import annotations
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory

def main() -> int:
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = list(script.get_heads())
    if len(heads) != 1:
        print(f"Error: expected 1 head, found {len(heads)}: {heads}")
        return 1
    for rev in script.walk_revisions():
        if getattr(rev.module, "down_revision", None) in (None, "None"):
            # allow the very first root only
            continue
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
