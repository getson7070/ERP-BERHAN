#!/usr/bin/env python3
"""tools/linearize_migrations.py

Detects duplicate revision IDs, unknown down_revisions, and multiple heads.
Can generate a skeleton merge revision file to merge *current* heads.
This script writes to stdout; edit results before committing.

Usage:
  python tools/linearize_migrations.py --report
"""
from __future__ import annotations
import os, sys, ast, re, datetime, pathlib
from typing import Dict, List, Set, Tuple
from alembic.config import Config
from alembic.script import ScriptDirectory

def main():
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    revs = list(script.walk_revisions())
    ids = {}
    downs: Set[str] = set()
    for r in revs:
        ids.setdefault(r.revision, []).append(r.path)
        for d in (r.down_revision or [] if isinstance(r.down_revision, (tuple, list)) else [r.down_revision] if r.down_revision else []):
            downs.add(d)
    heads = list(script.get_heads())
    dups = {k:v for k,v in ids.items() if len(v) > 1}
    unknown_downs = [d for d in downs if d not in ids]

    print("== MIGRATION REPORT ==")
    print("heads:", heads)
    print("duplicates:", dups)
    print("unknown_downs:", unknown_downs)
    print("total revisions:", len(ids))

    if len(heads) > 1:
        now = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = f"migrations/versions/{now}_merge_heads_final.py"
        print("\nSUGGESTED MERGE REVISION (create this file):", fname)
        print("---8<--- CUT HERE ---8<---")
        print(f"""# Auto-generated merge of heads
# Created: {now} UTC
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "{now}_merge_heads_final"
down_revision = {tuple(heads)!r}
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
""")
        print("---8<--- CUT HERE ---8<---")

if __name__ == "__main__":
    main()
