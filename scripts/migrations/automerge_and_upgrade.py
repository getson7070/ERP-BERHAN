# scripts/migrations/automerge_and_upgrade.py
import subprocess, sys, re
from datetime import datetime, timezone

ALEMBIC = ["alembic", "-c", "alembic.ini"]

def run_capture(*argv):
    p = subprocess.run(argv, text=True, capture_output=True)
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    return p.returncode, out

def a(*args):
    # IMPORTANT: expand as separate args, not a nested tuple
    return run_capture(*ALEMBIC, *args)

def _parse_heads_verbose(s: str):
    ids, seen = [], set()
    for ln in s.splitlines():
        m = re.search(r"\bRev:\s+([A-Za-z0-9_]+)\s+\(head\b", ln)
        if m:
            rid = m.group(1)
            if rid not in seen:
                seen.add(rid); ids.append(rid)
    return ids

def get_heads():
    # Prefer quiet (pure IDs)
    rc, out = a("heads", "-q")
    if rc == 0:
        ids = [t for t in (tok.strip() for tok in out.split()) if re.fullmatch(r"[A-Za-z0-9_]+", t)]
        if ids:
            return list(dict.fromkeys(ids))
    # Fallback to verbose, then branches
    rc, out = a("heads", "--verbose")
    ids = _parse_heads_verbose(out)
    if ids:
        return ids
    rc, out = a("branches")
    return _parse_heads_verbose(out)

def merge_heads(heads):
    if len(heads) <= 1:
        return
    rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"[automerge] Multiple heads: {heads}. Creating merge {rid}", flush=True)
    rc, out = a("merge", "-m", f"Auto-merge heads {rid}", *heads)
    if rc != 0:
        print(out, file=sys.stderr)
        sys.exit(rc)

def diagnostics():
    for label, argv in [
        ("heads -q", ["heads","-q"]),
        ("heads --verbose", ["heads","--verbose"]),
        ("branches", ["branches"]),
        ("history --verbose", ["history","--verbose"]),
    ]:
        rc, out = a(*argv)
        print(f"$ alembic -c alembic.ini {label}\n{out}\n", flush=True)

def main():
    # pre-merge if needed
    heads = get_heads()
    if len(heads) > 1:
        merge_heads(heads)

    # try upgrade
    rc, out = a("upgrade", "head")
    if rc == 0:
        print("[upgrade] Database is up-to-date.", flush=True)
        return

    # still multiple heads? merge and retry once
    if "Multiple head revisions are present" in out:
        print("[upgrade] Multiple heads during upgrade; merging and retrying…", flush=True)
        heads = get_heads()
        if len(heads) > 1:
            merge_heads(heads)
        rc, out = a("upgrade", "head")
        if rc == 0:
            print("[upgrade] Success after merge.", flush=True)
            return

    # other errors → show diagnostics
    print(out, file=sys.stderr)
    diagnostics()
    sys.exit(rc)

if __name__ == "__main__":
    main()
