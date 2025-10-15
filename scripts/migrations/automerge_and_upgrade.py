import subprocess, sys, re
from datetime import datetime, timezone

ALEMBIC = ["alembic", "-c", "alembic.ini"]

def run_capture(*args):
    # Flatten any nested lists/tuples and ensure strings
    flat = []
    for a in args:
        if isinstance(a, (list, tuple)):
            flat.extend([str(x) for x in a])
        else:
            flat.append(str(a))
    p = subprocess.run(flat, text=True, capture_output=True)
    out = (p.stdout or "") + (( "\n" + p.stderr) if p.stderr else "")
    return p.returncode, out.strip()

def call_alembic(*args):
    rc, out = run_capture(ALEMBIC, list(args))
    label = " ".join(args)
    print(f"$ alembic -c alembic.ini {label}")
    print(out)
    return rc, out

def parse_heads(text):
    ids = []
    for line in text.splitlines():
        # take first token up to whitespace or '('
        m = re.match(r"^([0-9a-zA-Z_]+)", line.strip())
        if m:
            ids.append(m.group(1))
    # unique, preserve order
    seen = set()
    uniq = []
    for r in ids:
        if r not in seen:
            seen.add(r); uniq.append(r)
    return uniq

def get_heads():
    rc, out = call_alembic("heads", "-q")
    # Alembic prints warnings to stderr; we already merged stdout+stderr
    return parse_heads(out)

def merge_heads(heads):
    # protect against bad inputs like labels from 'branches --verbose'
    heads = [h for h in heads if re.match(r"^[0-9a-zA-Z_]+$", h)]
    if len(heads) <= 1:
        return True
    rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"[automerge] Multiple heads detected: {heads}. Creating merge {rid}")
    rc, out = call_alembic("merge", "-m", f"Converge heads {rid}", *heads)
    return rc == 0

def upgrade_head():
    rc, out = call_alembic("upgrade", "head")
    return rc == 0

def main():
    heads = get_heads()
    if len(heads) > 1:
        if not merge_heads(heads):
            print("FAILED: could not create merge revision. Fix duplicate revision IDs or placeholder files.", file=sys.stderr)
            sys.exit(1)
    if not upgrade_head():
        # One more try in case new heads appeared after the merge
        heads = get_heads()
        if len(heads) > 1:
            if not merge_heads(heads) or not upgrade_head():
                sys.exit(1)
        else:
            sys.exit(1)
    print("[upgrade] Success")

if __name__ == "__main__":
    main()
