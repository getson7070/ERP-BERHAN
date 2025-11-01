#!/usr/bin/env python3
import re, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "erp"
code_files = [p for p in APP_ROOT.rglob("*.py") if "__pycache__" not in p.parts]
template_files = list((APP_ROOT / "templates").rglob("*.html"))

bp_var = re.compile(r'^\s*([A-Za-z_]\w*)\s*=\s*Blueprint\s*\(\s*[\'"]([\w\-]+)[\'"]', re.M)
bp_reg = re.compile(r'register_blueprint\s*\(\s*([\w\.]+)')
defined, registered = {}, set()

for pf in code_files:
    try: txt = pf.read_text(encoding="utf-8", errors="ignore")
    except: continue
    for m in bp_var.finditer(txt):
        v, name = m.group(1), m.group(2)
        defined.setdefault(name, []).append((pf, v))
    for m in bp_reg.finditer(txt):
        registered.add(m.group(1).split(".")[-1])

registered_names = set()
for short in registered:
    for name, sites in defined.items():
        for f,v in sites:
            if v == short:
                registered_names.add(name)

unregistered = sorted(set(defined.keys()) - registered_names)

tpl_unknown = []
tpl_pat = re.compile(r"url_for\(\s*[\'\"]([\w\-]+)\.")
for tf in template_files:
    try: t = tf.read_text(encoding="utf-8", errors="ignore")
    except: continue
    for m in tpl_pat.finditer(t):
        bp = m.group(1)
        if bp not in defined:
            tpl_unknown.append((str(tf), bp))

status = 0
if unregistered:
    print("[WARN] Unregistered blueprints:", ", ".join(unregistered[:20]))
if tpl_unknown:
    status = 2
    print("[FAIL] Templates reference unknown blueprints (sample):")
    for path, bp in tpl_unknown[:10]:
        print("   -", bp, "in", path)

print("[OK] Preflight checks passed." if status==0 else f"[EXIT] Preflight checks completed with status {status}.")
sys.exit(status)
