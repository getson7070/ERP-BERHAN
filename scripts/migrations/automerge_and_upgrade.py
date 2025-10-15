import subprocess, sys, re
from datetime import datetime, timezone
from pathlib import Path

ALEMBIC = ["alembic", "-c", "alembic.ini"]

def run_capture(*argv):
    p = subprocess.run(argv, text=True, capture_output=True)
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    return p.returncode, out

def a(*args):
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
    rc, out = a("heads", "-q")
    if rc == 0:
        ids = [t for t in (tok.strip() for tok in out.split()) if re.fullmatch(r"[A-Za-z0-9_]+", t)]
        if ids:
            return list(dict.fromkeys(ids))
    rc, out = a("heads", "--verbose")
    ids = _parse_heads_verbose(out)
    if ids:
        return ids
    rc, out = a("branches")
    return _parse_heads_verbose(out)

def write_merge_revision(migrations_path: Path, heads):
    # generate id
    rid = "automerge_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    fname = f"{rid}_auto_merge_heads.py"
    target = migrations_path / "versions" / fname
    target.parent.mkdir(parents=True, exist_ok=True)
    body = f""""""Auto-merge heads {', '.join(heads)}"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "{rid}"
down_revisions = {tuple(heads)!r}
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
"""
    target.write_text(body)
    print(f"[automerge] Wrote merge revision {target}")

def normalize_duplicates(migrations_path: Path):
    # Rename duplicate revision IDs to unique ones to avoid Alembic complaining.
    versions = migrations_path / "versions"
    by_rev = {}
    for f in versions.glob("*.py"):
        txt = f.read_text(errors="ignore")
        m = re.search(r"^revision\s*=\s*['\"]([A-Za-z0-9_]+)['\"]", txt, re.M)
        if not m:
            continue
        rev = m.group(1)
        by_rev.setdefault(rev, []).append(f)

    for rev, files in by_rev.items():
        if len(files) <= 1:
            continue
        # Keep the first as canonical
        canon = files[0]
        extras = files[1:]
        for idx, ef in enumerate(extras, start=1):
            newrev = f"{rev}_dup{idx}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            txt = ef.read_text(errors="ignore")
            txt = re.sub(r"^revision\s*=\s*['\"]([A-Za-z0-9_]+)['\"]", f"revision = '{newrev}'", txt, flags=re.M)
            # filename rename to include newrev
            base = ef.name
            # replace leading token up to first underscore with newrev
            parts = base.split("_", 1)
            newname = f"{newrev}_{parts[1] if len(parts)>1 else 'renamed.py'}"
            newpath = ef.with_name(newname)
            newpath.write_text(txt)
            ef.unlink()
            print(f"[normalize] Renamed duplicate {ef.name} -> {newname}")

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
    # Make sure we run inside repo root (find migrations dir)
    mig = Path("migrations")
    if not mig.exists():
        print("[error] migrations/ not found", file=sys.stderr)
        sys.exit(2)

    # Step 1: normalize duplicate revision IDs
    normalize_duplicates(mig)

    # Step 2: pre-merge if multiple heads
    heads = get_heads()
    if len(heads) > 1:
        write_merge_revision(mig, heads)

    # Step 3: upgrade
    rc, out = a("upgrade", "head")
    if rc == 0:
        print("[upgrade] Database is up-to-date.", flush=True)
        return

    # If still multiple heads, generate another merge and retry once
    if "Multiple head revisions are present" in out:
        print("[upgrade] Multiple heads during upgrade; writing merge revision and retrying…", flush=True)
        heads = get_heads()
        if len(heads) > 1:
            write_merge_revision(Path("migrations"), heads)
        rc, out = a("upgrade", "head")
        if rc == 0:
            print("[upgrade] Success after merge.", flush=True)
            return

    print(out, file=sys.stderr)
    diagnostics()
    sys.exit(rc)

if __name__ == "__main__":
    main()
