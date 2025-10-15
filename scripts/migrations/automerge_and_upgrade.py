# scripts/migrations/automerge_and_upgrade.py
import subprocess, sys, re
from datetime import datetime, timezone

ALEMBIC = ["alembic", "-c", "alembic.ini"]  # be explicit about config location

def sh(*args):
    return subprocess.run(args, text=True, capture_output=True)

def heads_quiet():
    """Ground truth: only real head IDs, one per line."""
    r = sh(*ALEMBIC, "heads", "-q")
    if r.returncode != 0:
        return []
    # keep only bare ids
    ids = []
    for ln in r.stdout.splitlines():
        tok = ln.strip()
        if re.fullmatch(r"[A-Za-z0-9_]+", tok):
            ids.append(tok)
    # de-dupe
    seen = set(); out = []
    for x in ids:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def heads_verbose_only_heads():
    """Fallback: parse ONLY lines like 'Rev: <id> (head...)' from --verbose output."""
    r = sh(*ALEMBIC, "heads", "--verbose")
    if r.returncode != 0:
        return []
    ids = []
    for ln in r.stdout.splitlines():
        m = re.match(r"^\s*Rev:\s+([A-Za-z0-9_]+)\s+\(head\b", ln)
        if m:
            ids.append(m.group(1))
    seen = set(); out = []
    for x in ids:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def get_heads_strict():
    q = heads_quiet()
    if q:
        return q
    v = heads_verbose_only_heads()
    return v

def merge_heads(heads):
    if len(heads) <= 1:
        return False
    rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"[automerge] Multiple heads detected: {heads}. Creating merge {rid}", flush=True)
    subprocess.check_call([*ALEMBIC, "merge", "-m", f"Auto-merge heads {rid}", *heads])
    return True

def try_upgrade_with_retry():
    """
    Try upgrade; if it fails due to 'Multiple head revisions', merge strictly-detected heads and retry once.
    """
    try:
        subprocess.check_call([*ALEMBIC, "upgrade", "head"])
        return
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or "") + "\n" + (e.stdout or "")
        if "Multiple head revisions are present" not in msg:
            # not our class of error; re-raise
            raise
        # detect and merge heads, then retry once
        heads = get_heads_strict()
        # intersect with quiet heads if available to ensure they are true heads
        q = heads_quiet()
        if q:
            heads = [h for h in heads if h in set(q)]
        heads = list(dict.fromkeys(heads))
        if len(heads) <= 1:
            # as a last resort, fall back to quiet heads directly
            heads = q
        if len(heads) > 1:
            merge_heads(heads)
        subprocess.check_call([*ALEMBIC, "upgrade", "head"])

def main():
    # pre-merge if we definitely see >1 heads
    heads = get_heads_strict()
    q = heads_quiet()
    if q and heads:
        heads = [h for h in heads if h in set(q)]  # keep only true heads
    heads = list(dict.fromkeys(heads))
    if len(heads) > 1:
        merge_heads(heads)

    # upgrade; if Alembic still finds multiple heads at runtime, we retry once after merging
    try_upgrade_with_retry()

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        sys.exit(e.returncode)
