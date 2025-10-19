import os, subprocess, sys, re, datetime, pathlib, textwrap

ALEMBIC = ["alembic", "-c", "alembic.ini"]

def run(*args):
    p = subprocess.run(list(args), text=True, capture_output=True)
    return p.returncode, (p.stdout or "") + (("\n"+p.stderr) if p.stderr else "")

def a(*sub):
    rc, out = run(*ALEMBIC, *sub)
    print(f"$ alembic -c alembic.ini {' '.join(sub)}\n{out}")
    return rc, out

def main():
    # Detect DB current revision
    rc, cur = a("current")
    if rc != 0:
        sys.exit(1)
    m = re.search(r'Current revision for .*?: ([0-9a-f]+)', cur)
    if not m:
        print("[repair] Could not detect current revision; abort.")
        sys.exit(2)
    current = m.group(1)

    # See if current exists in code history
    rc, hist = a("history")
    if current in hist:
        print("[repair] DB revision exists in code; no action.")
        sys.exit(0)

    # If DB has a ghost revision, create shim to re-attach
    ghost = current
    now = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    new_rev = f"shim_{now}"
    # Find a plausible parent: last line in history (base) or ask user to set env
    parent = os.getenv("REPAIR_PARENT_REVISION")
    if not parent:
        # crude guess: find last 'Rev:' entry
        revs = re.findall(r'Rev: ([0-9a-z_]+)', hist)
        parent = revs[-1] if revs else None
    if not parent:
        print("[repair] Could not guess parent. Set REPAIR_PARENT_REVISION.")
        sys.exit(3)

    body = textwrap.dedent(f"""
        """Shim to reconnect DB ghost revision.
        Revision ID: {new_rev}
        Revises: {ghost}
        Create Date: {now}
        """
        from alembic import op
        import sqlalchemy as sa
        revision = "{new_rev}"
        down_revision = "{ghost}"
        branch_labels = None
        depends_on = None
        def upgrade():
            pass
        def downgrade():
            pass
    """)

    target = pathlib.Path("migrations/versions") / f"{new_rev}_shim.py"
    target.write_text(body, encoding="utf-8")
    print(f"[repair] Wrote {target} linking to ghost {ghost}. Now run: alembic upgrade head")

if __name__ == "__main__":
    sys.exit(main())


