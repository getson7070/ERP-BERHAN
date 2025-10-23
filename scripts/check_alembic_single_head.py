#!/usr/bin/env python3
# This script fails CI if the Alembic migrations directory has more than one head.
# It does NOT connect to a database and will not create any migrations.
import subprocess, sys

def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return r.returncode, r.stdout.strip()

def main():
    code, out = run(["alembic", "heads", "-q"])
    if code != 0:
        print("ERROR: failed to run 'alembic heads -q'\n\n" + out)
        sys.exit(1)

    heads = [line.strip() for line in out.splitlines() if line.strip()]
    unique_heads = []
    for h in heads:
        if h not in unique_heads:
            unique_heads.append(h)

    count = len(unique_heads)
    print(f"Detected Alembic heads: {count}")
    for h in unique_heads:
        print(f"  - {h}")

    if count > 1:
        print("\nFAIL: Multiple migration heads detected. Please create a merge revision to converge to a single head.")
        sys.exit(2)

    if count == 0:
        print("WARN: No heads detected. Ensure Alembic is configured correctly and versions exist.")
        sys.exit(0)

    print("PASS: Single migration head enforced.")
    sys.exit(0)

if __name__ == "__main__":
    main()
