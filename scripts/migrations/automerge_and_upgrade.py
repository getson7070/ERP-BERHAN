import subprocess
from datetime import datetime

def sh(*args):
    return subprocess.run(args, text=True, capture_output=True)

def parse_heads_output(text):
    revs = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln: continue
        if ln.startswith("Rev:"):
            revs.append(ln.split("Rev:",1)[1].strip())
        elif " " not in ln and len(ln) >= 6 and ln.isalnum():
            revs.append(ln)
    return list(dict.fromkeys(revs))

def main():
    r = sh("alembic", "heads", "--verbose")
    heads_text = r.stdout if r.returncode == 0 else ""
    revs = parse_heads_output(heads_text)
    if not revs:
        r2 = sh("alembic", "heads")  # fallback
        revs = parse_heads_output(r2.stdout)
    if len(revs) > 1:
        rid = "automerge_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
        print(f"[automerge] Multiple heads detected: {revs}. Creating merge {rid}", flush=True)
        subprocess.check_call(["alembic", "merge", "-m", f"Auto-merge heads {rid}", *revs])
    subprocess.check_call(["alembic", "upgrade", "head"])

if __name__ == "__main__":
    main()