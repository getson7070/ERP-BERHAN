
import subprocess, sys, re
from datetime import datetime

ALEMBIC = ("alembic", "-c", "alembic.ini")

def run_capture(*argv):
    p = subprocess.run(argv, text=True, capture_output=True)
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    return p.returncode, out

def alembic(*args):
    return run_capture(*ALEMBIC, *args)

def get_heads():
    # Prefer quiet output if supported (global -q must precede command)
    rc, out = alembic("-q", "heads")
    if rc != 0 or not out.strip():
        rc, out = alembic("heads", "--verbose")
        if rc != 0:
            print(out, flush=True)
            sys.exit(1)
        revs = re.findall(r"^Rev:\s*([0-9a-f_]+)\b", out, re.M)
        return revs
    revs = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return revs

def diagnostics():
    for cmd in (("heads","--verbose"), ("branches",), ("history","--verbose")):
        rc, out = alembic(*cmd)
        print(f"$ alembic -c alembic.ini {' '.join(cmd)}\n{out}\n", flush=True)

def main():
    # Pre-check for dangling parent revisions in merge files
    rc, out = alembic("history", "--verbose")
    if rc != 0:
        print(out, flush=True)
    missing = re.findall(r"Can't locate revision identified by '([0-9a-f_]+)'", out)
    if missing:
        print(out, flush=True)
        sys.exit(1)

    heads = get_heads()
    if len(heads) <= 1:
        print("[upgrade] Single head detected; running upgrade head…", flush=True)
        rc, out = alembic("upgrade", "head")
        print(out, flush=True)
        if rc != 0:
            diagnostics()
            sys.exit(1)
        print("[upgrade] Database is up-to-date.", flush=True)
        return

    print(f"[automerge] Multiple heads detected: {heads}. Creating merge.", flush=True)
    rid = "automerge_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    rc, out = alembic("merge", "-m", f"Auto-merge heads {rid}", *heads)
    print(out, flush=True)
    if rc != 0:
        diagnostics()
        sys.exit(1)

    rc, out = alembic("upgrade", "head")
    print(out, flush=True)
    if rc != 0:
        diagnostics()
        sys.exit(1)
    print("[upgrade] Success after merge.", flush=True)

if __name__ == "__main__":
    main()
