#!/usr/bin/env python3
import re, sys
from pathlib import Path
from collections import defaultdict

VERSIONS = Path(__file__).resolve().parents[2] / "migrations" / "versions"
rev_to_files = defaultdict(list)

for f in VERSIONS.glob("*.py"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^revision\s*=\s*['\"]([0-9A-Za-z_]+)['\"]", t, re.M)
    rid = m.group(1) if m else f.name.split("_")[0]
    rev_to_files[rid].append(f.name)

dupes = {k:v for k,v in rev_to_files.items() if len(v)>1}
if dupes:
    print("Duplicate revision ids detected:\n", dupes)
    sys.exit(1)
print("No duplicate revision ids detected.")
