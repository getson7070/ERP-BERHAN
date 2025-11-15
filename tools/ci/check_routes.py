# -*- coding: utf-8 -*-
import sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in map(str, sys.path):
    sys.path.insert(0, str(ROOT))

from erp import create_app  # noqa: E402

app = create_app()

out_dir = ROOT / "tools" / "reports"
out_dir.mkdir(parents=True, exist_ok=True)
out = out_dir / "routes.txt"

with out.open("w", encoding="utf-8") as f:
    for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
        methods = ",".join(sorted(m for m in r.methods if m not in ("HEAD", "OPTIONS")))
        f.write(f"{r.endpoint:40s}  {methods:25s}  {r.rule}\n")

print(f"Wrote {out}")