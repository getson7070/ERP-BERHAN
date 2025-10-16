#!/usr/bin/env python3
import os, re, shlex, subprocess, sys, time

ALEMBIC = ["alembic", "-c", "alembic.ini"]

def run(*args, allow_fail=False):
    cmd = list(args)
    print("$", " ".join(shlex.quote(a) for a in cmd), flush=True)
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.stdout:
        print(p.stdout, end="")
    if p.stderr:
        print(p.stderr, end="")
    if p.returncode and not allow_fail:
        sys.exit(p.returncode)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def parse_heads(out: str):
    revs = []
    for ln in out.splitlines():
        m = re.match(r"^Rev:\s+([0-9a-f_]+)\s+\(head", ln)
        if m:
            revs.append(m.group(1))
            continue
        t = ln.strip()
        if re.fullmatch(r"[0-9a-f_]{6,}", t):
            revs.append(t)
    return sorted(set(revs))

def get_heads():
    rc, out = run(*ALEMBIC, "heads", "--verbose", allow_fail=True)
    if rc != 0:
        rc, out = run(*ALEMBIC, "heads", allow_fail=True)
    return parse_heads(out)

def upgrade_head():
    rc, out = run(*ALEMBIC, "upgrade", "head", allow_fail=True)
    if rc == 0:
        print("[upgrade] success", flush=True); return True, ""
    ol = (out or "").lower()
    if "multiple head revisions" in ol: return False, "multiple_heads"
    if "can't locate revision" in ol or "can't locate" in ol: return False, "missing_revision"
    if "lock timeout" in ol or "statement timeout" in ol: return False, "db_timeout"
    return False, out or "unknown_error"

def main():
    print("[predeploy] start", flush=True)
    run(*ALEMBIC, "current", allow_fail=True)
    run(*ALEMBIC, "history", "--verbose", allow_fail=True)

    ok, why = upgrade_head()
    if ok: return

    if why == "missing_revision":
        print("[fatal] DB references a revision not present in code. Create a no-op shim with the missing revision id and correct down_revision, commit, redeploy.", flush=True)
        sys.exit(1)

    if why == "multiple_heads":
        heads = get_heads()
        print(f"[heads] {', '.join(heads) or '(none)'}", flush=True)
        if os.getenv("AUTO_MERGE_MIGRATIONS") == "1":
            rid = "automerge_" + time.strftime("%Y%m%d%H%M%S", time.gmtime())
            print(f"[merge] creating {rid}", flush=True)
            run(*ALEMBIC, "merge", "-m", f"Auto-merge heads {rid}", *heads)
            ok2, why2 = upgrade_head()
            if ok2: 
                print("[merge+upgrade] success", flush=True); sys.exit(0)
            print(f"[merge+upgrade] failed: {why2}", flush=True); sys.exit(1)
        else:
            print("[abort] Multiple heads. Commit a manual merge or set AUTO_MERGE_MIGRATIONS=1 in staging only.", flush=True)
            sys.exit(1)

    if why == "db_timeout":
        print("[fatal] Migration hit DB timeout; split heavy DDL, use CONCURRENTLY for indexes, avoid data backfills in migrations.", flush=True)
        sys.exit(1)

    print(f"[fatal] alembic upgrade failed: {why}", flush=True); sys.exit(1)

if __name__ == "__main__":
    main()
