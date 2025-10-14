#!/usr/bin/env python3
import re, sys, subprocess, json
from pathlib import Path

mig_dir = Path("migrations/versions")
bad = []
placeholders = re.compile(r"(rev\d+|<head|\.\.\.|"None"|'None')")

for py in mig_dir.glob("*.py"):
    txt = py.read_text(errors="ignore")
    m = re.search(r"^down_revision\s*=\s*(.+)$", txt, re.M)
    if not m: 
        bad.append((py.name, "missing down_revision"))
        continue
    line = m.group(1)
    if placeholders.search(line):
        bad.append((py.name, f"placeholder in down_revision: {line.strip()}"))

# alembic heads must be exactly 1 after generating a temp env
# caller should run this script in CI inside a temp DB container
if bad:
    for f,msg in bad:
        print(f"[MIG-CHECK] {f}: {msg}")
    sys.exit(1)
