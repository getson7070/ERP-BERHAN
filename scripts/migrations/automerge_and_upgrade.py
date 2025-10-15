# scripts/migrations/automerge_and_upgrade.py
import subprocess, sys, re
from datetime import datetime, timezone

def sh(*args):
    return subprocess.run(args, text=True, capture_output=True)

def parse_heads_verbose(text: str):
    # Only accept "Rev: <id>" lines to avoid "Parent:", "Branches", etc.
    revs = []
    for ln in text.splitlines():
        m = re.match(r"^\s*Rev:\s+([A-Za-z0-9_]+)", ln)
        if m:
            revs.append(m.group(1))
    # de-dupe preserve order
    out, seen = [], set()
    for r in revs:
        if r not in seen:
            seen.add(r); out.append(r)
    return out

def parse_heads_fallback(text: str):
    # Fallback when --verbose not available; filter out words and colon lines
    stopwords = {"parent", "branches", "path", "merges", "auto-merge", "add"}
    revs = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or ":" in s:
            continue
        # take first token, strip annotations like "(head)"
        tok = s.split()[0]
        tok = tok.split("(")[0].strip().rstrip(",")
        if not tok or not re.match(r"^[A-Za-z0-9_]+$", tok):
            continue
        if tok.lower() in stopwords:
            continue
        revs.append(tok)
    # de-dupe
    out, seen = [], set()
    for r in revs:
        if r not in seen:
            seen.add(r); out.append(r)
    return out

def get_heads():
    # Prefer --verbose and parse only "Rev:" lines
    r = sh("alembic", "heads", "--verbose")
    if r.returncode == 0 and r.stdout.strip():
        revs = parse_heads_verbose(r.stdout)
        if revs:
            return revs
    # Fallback to non-verbose parsing with strict filters
    r = sh("alembic", "heads")
    if r.returncode == 0 and r.stdout.strip():
        revs = parse_heads_fallback(r.stdout)
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
