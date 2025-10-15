# tools/dedupe_alembic.py
import argparse, re, sys, pathlib
VERS = pathlib.Path("migrations/versions")

def scan():
    by_rev = {}
    if not VERS.exists():
        print("migrations/versions not found", file=sys.stderr)
        return {}
    for f in VERS.glob("*.py"):
        txt = f.read_text(errors="ignore")
        m = re.search(r"^revision\s*=\s*['\"]([A-Za-z0-9_]+)['\"]", txt, re.M)
        if not m:
            continue
        rev = m.group(1)
        by_rev.setdefault(rev, []).append(f)
    return by_rev

def main():
    by_rev = scan()
    dupes = {k:v for k,v in by_rev.items() if len(v) > 1}
    if not dupes:
        print("No duplicate revision IDs detected.")
        return 0
    print("Duplicate revision IDs:")
    for rev, paths in dupes.items():
        print(f"  {rev}:")
        for p in paths:
            print(f"    - {p}")
    if "--check-only" in sys.argv:
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
