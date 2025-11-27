"""Automatic Alembic head repair and drift normalisation.

This helper replaces the manual stamping/merge steps documented in
`MIGRATIONS_TODO.txt` and `MIGRATIONS_CONSOLIDATION.md`. It will:

1. Ensure the target database exists (using ``tools/db_preflight.py`` when
   a database URL is available).
2. Detect multiple Alembic heads and auto-merge them into a single linear
   chain.
3. Stamp an untracked database to ``head`` when the ``alembic_version``
   table is missing or empty.
4. Upgrade the schema to the latest migration.

Run this from the repo root:

```
python tools/repair_migration_heads.py
```

Use ``--dry-run`` to see planned actions without mutating the database.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Iterable

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = ROOT / "alembic.ini"


def _run(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    return result


def _resolve_database_url() -> str | None:
    env_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if env_url:
        return env_url

    if not ALEMBIC_INI.exists():
        return None

    parser = ConfigParser()
    parser.read(ALEMBIC_INI)
    return parser.get("alembic", "sqlalchemy.url", fallback=None)


def _ensure_database(env: dict[str, str], *, dry_run: bool) -> None:
    db_url = env.get("DATABASE_URL") or env.get("SQLALCHEMY_DATABASE_URI")
    preflight = ROOT / "tools" / "db_preflight.py"

    if not db_url:
        print("[repair] No database URL provided; skipping DB creation step.")
        return

    if not preflight.exists():
        print("[repair] db_preflight.py missing; skipping DB creation step.")
        return

    if dry_run:
        print("[repair] DRY-RUN: would run db_preflight.py to create DB if missing.")
        return

    print("[repair] Ensuring database exists via db_preflight.py …")
    proc = _run([sys.executable, str(preflight)], env)
    if proc.returncode != 0:
        raise SystemExit(proc.stdout + proc.stderr)


def _file_heads() -> list[str]:
    cfg = Config(str(ALEMBIC_INI))
    script_dir = ScriptDirectory.from_config(cfg)
    return script_dir.get_heads()


def _detect_heads(env: dict[str, str]) -> tuple[list[str], str]:
    """Return alembic heads as reported by ``alembic heads``.

    The previous implementation failed to parse the output because ``alembic
    heads`` prefixes each revision line with ``Rev:`` (for example,
    ``Rev: abcd1234 (head)``). We normalise the pattern to capture both the
    ``Rev:`` prefix and any optional leading whitespace.
    """

    proc = _run(["alembic", "heads", "-v"], env)
    if proc.returncode != 0:
        raise SystemExit(proc.stdout + proc.stderr)

    # Example lines:
    # Rev: abcd1234 (head)
    # Path: /.../migrations/versions/abcd1234_example.py
    heads = re.findall(r"^\s*Rev:\s*([0-9a-f]+)\s+\(head\)", proc.stdout, flags=re.MULTILINE)
    return heads, proc.stdout.strip()


def _merge_heads(heads: Iterable[str], env: dict[str, str], *, dry_run: bool) -> None:
    heads = list(heads)
    if len(heads) <= 1:
        return

    print(f"[repair] Detected multiple heads: {heads}")
    if dry_run:
        print("[repair] DRY-RUN: would run alembic merge to linearise heads.")
        return

    merge_cmd = ["alembic", "merge", "-m", "auto-merge heads"] + heads
    proc = _run(merge_cmd, env)
    if proc.returncode != 0:
        raise SystemExit(proc.stdout + proc.stderr)
    print(proc.stdout.strip())


def _current_revision(env: dict[str, str]) -> tuple[list[str], str]:
    proc = _run(["alembic", "current", "--verbose"], env)
    stdout_stderr = (proc.stdout or "") + (proc.stderr or "")
    revs = re.findall(r"([0-9a-f]{12,})", stdout_stderr)
    return revs, stdout_stderr.strip()


def _stamp_head(env: dict[str, str], *, dry_run: bool) -> None:
    if dry_run:
        print("[repair] DRY-RUN: would stamp database to head (no alembic_version entry).")
        return

    proc = _run(["alembic", "stamp", "head"], env)
    if proc.returncode != 0:
        raise SystemExit(proc.stdout + proc.stderr)
    print(proc.stdout.strip())


def _upgrade_head(env: dict[str, str], *, dry_run: bool) -> None:
    if dry_run:
        print("[repair] DRY-RUN: would upgrade database to head.")
        return

    proc = _run(["alembic", "upgrade", "head"], env)
    if proc.returncode != 0:
        raise SystemExit(proc.stdout + proc.stderr)
    print(proc.stdout.strip())


def repair_heads(dry_run: bool = False) -> None:
    if not ALEMBIC_INI.exists():
        raise SystemExit("alembic.ini not found; cannot repair migrations.")

    env = os.environ.copy()
    db_url = _resolve_database_url()
    if db_url:
        env.setdefault("DATABASE_URL", db_url)

    _ensure_database(env, dry_run=dry_run)

    file_heads = _file_heads()
    if dry_run:
        print(f"[repair] DRY-RUN: file-defined heads: {file_heads}")
        if len(file_heads) > 1:
            print("[repair] DRY-RUN: multiple heads would be merged automatically.")
        print("[repair] DRY-RUN: would stamp database if no revision is recorded, then upgrade to head.")
        return

    _merge_heads(file_heads, env, dry_run=dry_run)

    heads, heads_output = _detect_heads(env)
    print(heads_output)

    revs, current_output = _current_revision(env)
    print(current_output)
    if not revs:
        print("[repair] No current revision detected; stamping to head …")
        _stamp_head(env, dry_run=dry_run)

    _upgrade_head(env, dry_run=dry_run)
    print("[repair] Migration chain repaired and upgraded to head ✅")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-merge and normalise Alembic heads.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without mutating the database.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    repair_heads(dry_run=args.dry_run)


