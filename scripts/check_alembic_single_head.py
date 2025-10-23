#!/usr/bin/env python3
import sys
from pathlib import Path

def find_versions_dirs(root: Path):
    # Any folder named "versions" under an "alembic" dir is a candidate
    candidates = []
    for v in root.rglob("versions"):
        if (v.parent / "env.py").exists():
            candidates.append(v)
    return candidates

def check_single_heads(versions_dir: Path) -> list[str]:
    # Use Alembic's script loader directly from the migration dir
    from alembic.script import ScriptDirectory
    script = ScriptDirectory(str(versions_dir.parent))
    heads = list(script.get_heads())
    if len(heads) <= 1:
        return []
    return heads

def main():
    repo_root = Path(__file__).resolve().parents[1]
    candidates = find_versions_dirs(repo_root)
    if not candidates:
        print("ERROR: No Alembic migrations found (no */alembic/versions directories).", file=sys.stderr)
        sys.exit(2)

    failures = []
    for vdir in candidates:
        heads = check_single_heads(vdir)
        if heads:
            failures.append((vdir, heads))

    if failures:
        print("FAIL: Multiple heads detected.")
        for vdir, heads in failures:
            print(f" - {vdir}: {heads}")
        sys.exit(1)

    print("OK: Single head per migration tree.")
    sys.exit(0)

if __name__ == "__main__":
    main()