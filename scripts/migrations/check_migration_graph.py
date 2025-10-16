#!/usr/bin/env python3
import glob, re, sys
revs, owners, down = {}, {}, {}
problems = 0
for p in glob.glob("migrations/versions/*.py"):
    try: text = open(p, encoding="utf-8").read()
    except Exception as e:
        print(f"[error] cannot read {p}: {e}"); problems += 1; continue
    r_m = re.search(r"^revision\s*=\s*['\"]([0-9a-f_]+)['\"]", text, re.M)
    d_m = re.search(r"^down_revision\s*=\s*(['\"][^'\"]+['\"]|None)", text, re.M)
    if not r_m:
        print(f"[error] {p}: missing 'revision'"); problems += 1; continue
    r = r_m.group(1); d = d_m.group(1) if d_m else "None"
    if r in revs:
        print(f"[dup] revision {r} appears in both {owners[r]} and {p}"); problems += 1
    revs[r] = p; owners[r] = p; down[r] = d.strip("'\"")
for r, d in down.items():
    if d != "None" and d not in revs:
        print(f"[missing-parent] {r} -> down_revision {d} not found on disk"); problems += 1
if problems: print(f"[result] FAIL with {problems} problem(s)"); sys.exit(1)
print("[result] OK")
