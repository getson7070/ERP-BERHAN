#!/usr/bin/env python3
"""Robust pre-deploy migration runner.
- Detects true Alembic heads via `alembic --verbose heads`
- If multiple heads, generates a merge revision and retries upgrade
- Logs everything; avoids brittle parsing and invalid CLI flags
- Fails loudly if database references a revision that is not present in code
"""
import subprocess, sys, re
from datetime import datetime, timezone

ALEMBIC = ("alembic", "-c", "alembic.ini")

def run(*argv):
    p = subprocess.run(argv, text=True, capture_output=True)
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    return p.returncode, out.strip()

def a(*args):
    rc, out = run(*ALEMBIC, *args)
    print(f"$ alembic {' '.join(args)}\n{out}\n", flush=True)
    return rc, out

def parse_heads():
    rc, out = a("--verbose", "heads")
    if rc != 0:
        return rc, [], out
    # Example lines: 'Rev: 1234abcd (head)' or 'Rev: 1234abcd (head) (mergepoint)'
    heads = re.findall(r"Rev:\s+([0-9A-Za-z_]+)\s+\(head\)", out)
    # fall back to last token on 'Rev:' lines
    if not heads:
        heads = [m.group(1) for m in re.finditer(r"Rev:\s+([0-9A-Za-z_]+)", out)]
    # keep only token-like ids
    heads = [h for h in heads if re.fullmatch(r"[0-9A-Za-z_]+", h)]
    # de-dupe
    uniq = []
    for h in heads:
        if h not in uniq:
            uniq.append(h)
    return 0, uniq, out

import os

def merge_heads(heads):
    rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    msg = f"Auto-merge heads {', '.join(heads)} ({rid})"
    # Create a merge revision that points all heads into one
    return a("merge", "-m", msg, *heads)

def upgrade_head():
    return a("upgrade", "head")

def main():
    # Helpful context in logs
    a("branches")
    a("--verbose", "heads")

    rc, heads, _ = parse_heads()
    if rc != 0:
        sys.exit(rc)

    if len(heads) > 1:
        print(f"[automerge] Multiple heads detected: {heads}", flush=True)
        if os.getenv('AUTO_MERGE_MIGRATIONS','0') != '1':
            print('[automerge] SAFE_MODE: refusing to create a merge revision during deploy. Set AUTO_MERGE_MIGRATIONS=1 to enable.', flush=True)
            sys.exit(3)
        mrc, mout = merge_heads(heads)
        if mrc != 0:
            print("[automerge] Merge failed; aborting.", flush=True)
            sys.exit(mrc)

    urc, uout = upgrade_head()
    if urc == 0:
        print("[upgrade] Database is up-to-date.", flush=True)
        sys.exit(0)

    # Known failure: DB points to a revision we don't have in code
    m = re.search(r"Can't locate revision identified by '([0-9A-Za-z_]+)'", uout)
    if m:
        missing = m.group(1)
        print("[fatal] Database references a missing revision:", missing, flush=True)
        print("        Options:", flush=True)
        print("        1) Recreate DB or run `alembic stamp base && alembic upgrade head` on a fresh DB.", flush=True)
        print("        2) Add an empty shim migration with revision '%s' that points to the correct parent, then upgrade." % missing, flush=True)
        print("        3) Manually stamp the DB to a valid revision that exists in code (risky on non-empty DB).", flush=True)
        sys.exit(2)

    print("[fatal] Alembic upgrade failed for an unknown reason:", flush=True)
    print(uout, flush=True)
    sys.exit(1)

if __name__ == "__main__":
    main()
