#!/usr/bin/env python3
import os, re, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
apps = list(PROJECT_ROOT.glob('**/erp/__init__.py'))
if len(apps) > 1:
    print('[FAIL] Multiple erp packages:', [str(p.parent) for p in apps]); sys.exit(2)

bp_var = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*Blueprint\s*\(\s*[\'"]([A-Za-z0-9_\-]+)[\'"]', re.M)
bp_reg = re.compile(r'register_blueprint\s*\(\s*([A-Za-z0-9_\.]+)')
defined, registered = {}, set()

for pf in PROJECT_ROOT.rglob('*.py'):
    try: txt = pf.read_text(encoding='utf-8', errors='ignore')
    except: continue
    for m in bp_var.finditer(txt):
        v, name = m.group(1), m.group(2)
        defined.setdefault(name, []).append((pf, v))
    for m in bp_reg.finditer(txt):
        registered.add(m.group(1).split('.')[-1])

registered_names = set()
for short in registered:
    for name, sites in defined.items():
        for f,v in sites:
            if v == short:
                registered_names.add(name)

unregistered = sorted(set(defined.keys()) - registered_names)

tpl_unknown = []
tpl_pat = re.compile(r"url_for\(\s*[\'\"]([A-Za-z0-9_\-]+)\.")
for tf in PROJECT_ROOT.rglob('*.html'):
    try: t = tf.read_text(encoding='utf-8', errors='ignore')
    except: continue
    for m in tpl_pat.finditer(t):
        bp = m.group(1)
        if bp not in defined:
            tpl_unknown.append((str(tf), bp))

hardcoded_secrets = []; debug_true = []
secret_pat = re.compile(r"SECRET_KEY\s*=\s*[\'\"][^\'\"]+[\'\"]")
debug_pat  = re.compile(r"DEBUG\s*=\s*True")

for pf in PROJECT_ROOT.rglob('*.py'):
    try: t = pf.read_text(encoding='utf-8', errors='ignore')
    except: continue
    if secret_pat.search(t): hardcoded_secrets.append(str(pf))
    if debug_pat.search(t):  debug_true.append(str(pf))

status = 0
if unregistered:
    print('[WARN] Unregistered blueprints:', ', '.join(unregistered[:20]))
if tpl_unknown:
    status = 2
    print('[FAIL] Templates reference unknown blueprints (sample):')
    for path, bp in tpl_unknown[:10]:
        print('   -', bp, 'in', path)
if hardcoded_secrets:
    status = max(status,1); print('[WARN] Hardcoded SECRET_KEY in:', hardcoded_secrets[:10])
if debug_true:
    status = max(status,1); print('[WARN] DEBUG=True in:', debug_true[:10])

print('[OK] Preflight checks passed.' if status==0 else f'[EXIT] Preflight checks completed with status {status}.')
sys.exit(status)
