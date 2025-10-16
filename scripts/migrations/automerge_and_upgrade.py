#!/usr/bin/env python3
import sys, shlex, subprocess
from alembic.config import Config
from alembic.script import ScriptDirectory

ALEMBIC = ["alembic", "-c", "alembic.ini"]

def sh(args):
    print("+", " ".join(shlex.quote(x) for x in args), flush=True)
    p = subprocess.run(args)
    if p.returncode != 0:
        sys.exit(p.returncode)

def main():
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    if len(heads) > 1:
        print(f"Detected multiple heads: {heads}", flush=True)
        sh(ALEMBIC + ["merge", "-m", "automerge heads", *heads])
    else:
        print(f"Heads OK: {heads}", flush=True)
    sh(ALEMBIC + ["upgrade", "head"])

if __name__ == "__main__":
    main()
