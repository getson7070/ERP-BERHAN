
import re, sys
from pathlib import Path

VERS = Path("migrations/versions")

def scan():
    by_rev = {}
    if not VERS.exists():
        print("migrations/versions not found", file=sys.stderr)
        return {}
    for f in VERS.glob("*.py"):
        try:
            txt = f.read_text(errors="ignore")
        except Exception:
            continue
        m = re.search(r"^revision\s*=\s*['\"]([A-Za-z0-9_]+)['\"]", txt, re.M)
        if not m:
            continue
        rev = m.group(1)
        by_rev.setdefault(rev, []).append(f)
    return by_rev

def main():
    dupes = {rev:paths for rev, paths in scan().items() if len(paths) > 1}
    if not dupes:
        print("No duplicate revision IDs detected.")
        return 0
    print("Duplicate revision IDs:")
    for rev, paths in dupes.items():
        print(f"  {rev}:")
        for p in paths:
            print(f"    - {p}")
    return 2

if __name__ == "__main__":
    sys.exit(main())
