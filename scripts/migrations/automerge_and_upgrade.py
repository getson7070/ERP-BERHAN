# scripts/migrations/automerge_and_upgrade.py
import subprocess, sys, re
from datetime import datetime, timezone

def sh(*args):
    return subprocess.run(args, text=True, capture_output=True)

def heads_quiet():
    """Use the canonical source of truth: only real head IDs, one per line."""
    r = sh("alembic", "heads", "-q")
    if r.returncode != 0:
        return []
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]

def heads_verbose_marked():
    """Fallback: parse only lines like 'Rev: <id> (head ...)' from --verbose."""
    r = sh("alembic", "heads", "--verbose")
    if r.returncode != 0:
        return []
    out = []
    for ln in r.stdout.splitlines():
        m = re.match(r"^\s*Rev:\s+([A-Za-z0-9_]+)\s+\(head\b", ln)
        if m:
            out.append(m.group(1))
    # de-dupe preserve order
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x); res.append(x)
    return res

def get_heads_strict():
    # 1) Prefer -q (real heads only)
    q = heads_quiet()
    if q:
        return q
    # 2) Fallback to verbose (only '(head)' lines)
    v = heads_verbose_marked()
    if not v:
        return []
    # 3) If verbose returned something but -q was empty, trust verbose
    return v

def main():
    # Resolve heads strictly
    heads = get_heads_strict()
    # Extra safety: if both quiet and verbose are available, intersect with -q
    q = heads_quiet()
    if q and heads:
        heads = [h for h in heads if h in set(q)]

    # De-duplicate
    seen = set(); heads = [h for h in heads if not (h in seen or seen.add(h))]

    if len(heads) > 1:
        rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        print(f"[automerge] Multiple heads detected: {heads}. Creating merge {rid}", flush=True)
        subprocess.check_call(["alembic", "merge", "-m", f"Auto-merge heads {rid}", *heads])

    # Always upgrade to the final head after potential merge
    subprocess.check_call(["alembic", "upgrade", "head"])

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        sys.exit(e.returncode)
