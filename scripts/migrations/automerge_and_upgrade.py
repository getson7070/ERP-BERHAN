# scripts/migrations/automerge_and_upgrade.py
"""
Robust Alembic pre-deploy:
- Detect real head revisions even when Alembic prints extra text or warnings.
- Merge all heads into a single merge revision.
- Retry upgrade.
- On failure, print useful diagnostics and exit nonzero.
"""

from __future__ import annotations
import subprocess, sys, re
from datetime import datetime, timezone
from typing import List

ALEMBIC = ["alembic", "-c", "alembic.ini"]

def run(*args: str) -> tuple[int, str]:
    p = subprocess.run(args, text=True, capture_output=True)
    out = (p.stdout or "") + (("
" + p.stderr) if p.stderr else "")
    return p.returncode, out

def a(*args: str) -> tuple[int, str]:
    return run(*((*ALEMBIC,), *args))

def parse_heads_from_verbose(s: str) -> List[str]:
    ids = []
    for ln in s.splitlines():
        # Typical line: "Rev: 1a2b3c4d5e6f (head)"
        m = re.search(r"\bRev:\s+([A-Za-z0-9_]+)\s+\(head\b", ln)
        if m:
            ids.append(m.group(1))
    # Deduplicate keeping order
    seen = set(); out = []
    for x in ids:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def get_heads() -> List[str]:
    # First, try quiet (pure IDs). It may warn/return 0 in some setups.
    rc, out = a("heads", "-q")
    if rc == 0:
        ids = [tok.strip() for tok in out.split() if re.fullmatch(r"[A-Za-z0-9_]+", tok.strip())]
        if ids:
            return list(dict.fromkeys(ids))
    # Fallback to verbose parsing
    rc, out = a("heads", "--verbose")
    ids = parse_heads_from_verbose(out)
    if ids:
        return ids
    # Last resort: parse from "branches" output
    rc, out = a("branches")
    ids = parse_heads_from_verbose(out)
    return ids

def merge_heads(heads: List[str]) -> None:
    if len(heads) <= 1:
        return
    rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"[automerge] Multiple heads detected: {heads}. Creating merge {rid}", flush=True)
    rc, out = a("merge", "-m", f"Auto-merge heads {rid}", *heads)
    if rc != 0:
        print(out, file=sys.stderr)
        sys.exit(rc)

def diagnostics() -> None:
    cmds = [
        ("heads -q", ["heads", "-q"]),
        ("heads --verbose", ["heads", "--verbose"]),
        ("branches", ["branches"]),
        ("history --verbose", ["history", "--verbose"]),
    ]
    print("\n[diagnostics] Alembic state:", flush=True)
    for label, argv in cmds:
        rc, out = a(*argv)
        print(f"$ alembic -c alembic.ini {label}\n{out}\n", flush=True)

def upgrade_head_with_auto_merge() -> None:
    heads = get_heads()
    if len(heads) > 1:
        merge_heads(heads)

    rc, out = a("upgrade", "head")
    if rc == 0:
        print("[upgrade] Database is up-to-date at a single head.", flush=True)
        return

    # Look for the multiple-head message; if found, merge and retry once
    if "Multiple head revisions are present" in out:
        print("[upgrade] Multiple heads detected at upgrade time, attempting merge+retry…", flush=True)
        heads = get_heads()
        if len(heads) > 1:
            merge_heads(heads)
        rc2, out2 = a("upgrade", "head")
        if rc2 == 0:
            print("[upgrade] Success after merge.", flush=True)
            return
        print(out2, file=sys.stderr)
        diagnostics()
        sys.exit(rc2)

    # Other errors
    print(out, file=sys.stderr)
    diagnostics()
    sys.exit(rc)

def main() -> None:
    upgrade_head_with_auto_merge()

if __name__ == "__main__":
    main()
