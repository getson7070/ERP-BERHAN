import os, re, sys, pathlib, ast
from collections import defaultdict

ROOT = pathlib.Path(os.getcwd())
MIGR = None
for p in ROOT.rglob("migrations"):
    if (p / "env.py").exists() and (p / "versions").exists():
        MIGR = p
        break
if not MIGR:
    print("No migrations/ found.", file=sys.stderr)
    sys.exit(2)

versions = MIGR / "versions"
rev_to_file = {}
parents = defaultdict(set)
children = defaultdict(set)
dups = []
missing = []

def extract(fpath):
    txt = fpath.read_text(encoding="utf-8", errors="ignore")
    rev = None
    down = None
    m_rev = re.search(r'^\s*revision\s*=\s*['\"]([^'\"]+)['\"]', txt, re.M)
    if m_rev: rev = m_rev.group(1)
    m_down = re.search(r'^\s*down_revision\s*=\s*(.+)$', txt, re.M)
    if m_down:
        raw = m_down.group(1).strip()
        try:
            dv = ast.literal_eval(raw)
        except Exception:
            dv = raw.strip('"'' )
        down = dv
    return rev, down

files = sorted(versions.glob("*.py"))
for f in files:
    rev, down = extract(f)
    if not rev: 
        print(f"[warn] {f} has no revision id")
        continue
    if rev in rev_to_file:
        dups.append((rev, rev_to_file[rev], f))
    rev_to_file[rev] = f
    if down is None:
        continue
    if isinstance(down, (list, tuple)):
        for d in down:
            parents[rev].add(d)
            children[d].add(rev)
    else:
        parents[rev].add(down)
        children[down].add(rev)

all_revs = set(rev_to_file.keys())
for rev, ds in parents.items():
    for d in ds:
        if d not in all_revs:
            missing.append((rev, d, rev_to_file[rev]))

heads = [r for r in all_revs if len(children.get(r, set())) == 0]

for r, a, b in dups:
    print(f"[dup] revision {r} appears in both {a.name} and {b.name}")
for r, d, f in missing:
    print(f"[missing-parent] {f.name}: revision {r} points to down_revision {d} which is not present in versions/")
print(f"[heads] {len(heads)} head(s): {', '.join(heads)}")


