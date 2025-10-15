# scripts/migrations/automerge_and_upgrade.py
import subprocess, sys, re
from datetime import datetime, timezone

def sh(*args):
    return subprocess.run(args, text=True, capture_output=True)

def _parse_heads_lines(lines):
    revs = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        # forms seen in the wild:
        #   "Rev: 123abc (head)"
        #   "123abc (branchpoint)"
        #   "123abc"
        if s.startswith("Rev:"):
            parts = s.split()
            rid = parts[1] if len(parts) > 1 else ""
        else:
            rid = s.split()[0]
        rid = rid.split("(")[0].strip().rstrip(",")  # remove annotations, commas
        if rid:
            revs.append(rid)
    # de-dupe while preserving order
    out = []
    seen = set()
    for r in revs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out

def get_heads():
    for cmd in (["alembic", "heads", "-q"], ["alembic", "heads", "--verbose"], ["alembic", "heads"]):
        r = sh(*cmd)
        if r.returncode == 0 and r.stdout.strip():
            revs = _parse_heads_lines(r.stdout.splitlines())
            if revs:
                return revs
    return []

def main():
    heads = get_heads()
    if len(heads) > 1:
        rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        print(f"[automerge] Multiple heads detected: {heads}. Creating merge {rid}", flush=True)
        subprocess.check_call(["alembic", "merge", "-m", f"Auto-merge heads {rid}", *heads])
    subprocess.check_call(["alembic", "upgrade", "head"])

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        sys.exit(e.returncode)
