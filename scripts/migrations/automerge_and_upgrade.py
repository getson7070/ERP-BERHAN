#!/usr/bin/env python3
# AUTOMERGE_SCRIPT_VERSION=2025-10-15T20:20Z
import subprocess, sys, re
from datetime import datetime, timezone
from pathlib import Path

ALEMBIC = ("alembic", "-c", "alembic.ini")

def run_capture(*argv):
    p = subprocess.run(argv, text=True, capture_output=True)
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    return p.returncode, out

def a(*args):
    return run_capture(*ALEMBIC, *args)

def get_heads():
    # Try quiet heads first
    rc, out = a("heads", "-q")
    if rc == 0:
        ids = [t for t in out.split() if re.fullmatch(r"[A-Za-z0-9_]+", t)]
        if ids:
            return list(dict.fromkeys(ids))
    # Fallback to verbose parsing
    def parse_verbose(s):
        ids = []
        for ln in s.splitlines():
            m = re.search(r"\bRev:\s+([A-Za-z0-9_]+)\s+\(head\b", ln)
            if m:
                ids.append(m.group(1))
        return list(dict.fromkeys(ids))
    rc, out = a("heads", "--verbose")
    ids = parse_verbose(out)
    if ids:
        return ids
    rc, out = a("branches")
    return parse_verbose(out)

def normalize_duplicates(migrations_path: Path):
    versions = migrations_path / "versions"
    if not versions.exists():
        return
    by_rev = {}
    for f in versions.glob("*.py"):
        try:
            txt = f.read_text(errors="ignore")
        except Exception:
            continue
        m = re.search(r"^revision\s*=\s*['\"]([A-Za-z0-9_]+)['\"]", txt, re.M)
        if not m:
            continue
        rev = m.group(1)
        by_rev.setdefault(rev, []).append(f)
    for rev, files in by_rev.items():
        if len(files) <= 1:
            continue
        # Keep the first as canonical; rename others to unique revisions
        for idx, ef in enumerate(files[1:], start=1):
            try:
                txt = ef.read_text(errors="ignore")
            except Exception:
                continue
            newrev = f"{rev}_dup{idx}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            txt = re.sub(r"^revision\s*=.*$", f"revision = '{newrev}'", txt, flags=re.M)
            # Preserve the rest of the filename after the first underscore
            parts = ef.name.split("_", 1)
            tail = parts[1] if len(parts) > 1 else "renamed.py"
            newname = ef.with_name(f"{newrev}_{tail}")
            newname.write_text(txt)
            ef.unlink()
            print(f"[normalize] {ef.name} -> {newname.name}")

def write_merge_revision(migrations_path: Path, heads):
    rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    target = migrations_path / "versions" / f"{rid}_merge_heads.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = "Auto-merge heads: " + ", ".join(heads)
    body = (
        ' + doc + \n\n'
        "from alembic import op\n"
        "import sqlalchemy as sa\n\n"
        "# revision identifiers, used by Alembic.\n"
        f"revision = \"{rid}\"\n"
        f"down_revision = {tuple(heads)!r}\n"
        "branch_labels = None\n"
        "depends_on = None\n\n"
        "def upgrade():\n"
        "    pass\n\n"
        "def downgrade():\n"
        "    pass\n"
    )
    target.write_text(body)
    print(f"[automerge] wrote {target.name}")

def diagnostics():
    for label, argv in [
        ("heads -q", ("heads","-q")),
        ("heads --verbose", ("heads","--verbose")),
        ("branches", ("branches",)),
        ("history --verbose", ("history","--verbose")),
    ]:
        rc, out = a(*argv)
        print(f"$ alembic -c alembic.ini {label}\n{out}\n", flush=True)

def main():
    mig = Path("migrations")
    if not mig.exists():
        print("[error] migrations/ not found", file=sys.stderr)
        sys.exit(2)

    normalize_duplicates(mig)

    heads = get_heads()
    if len(heads) > 1:
        print(f"[automerge] Multiple heads detected: {heads}")
        write_merge_revision(mig, heads)

    rc, out = a("upgrade", "head")
    if rc == 0:
        print("[upgrade] ok")
        return

    if "Multiple head revisions are present" in out or "Multiple head revisions" in out:
        print("[upgrade] still multiple heads; merging again...")
        heads = get_heads()
        if len(heads) > 1:
            write_merge_revision(mig, heads)
        rc, out = a("upgrade", "head")
        if rc == 0:
            print("[upgrade] ok after merge")
            return

    print(out, file=sys.stderr)
    diagnostics()
    sys.exit(rc)

if __name__ == "__main__":
    main()
