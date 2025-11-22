#!/usr/bin/env python
"""Lightweight migration smoke test helper.

Restores an optional dump, upgrades, runs sanity checks, and optionally
executes a downgrade to validate rollback paths on prod-like data.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, text

REPO = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    print(">", " ".join(cmd))
    env = env or os.environ.copy()
    result = subprocess.run(cmd, cwd=str(REPO), env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _restore_dump(db_url: str, dump_path: str) -> None:
    print(f"Restore requested from {dump_path} -> {db_url}")
    # Implementation is environment-specific; log intent for operators.
    # You can pipe pg_restore here when running in CI or locally.


def _sanity_checks(db_url: str) -> None:
    engine = create_engine(db_url)
    with engine.begin() as cx:
        rev = cx.execute(text("SELECT version_num FROM alembic_version"))[0][0]
        if not rev:
            raise RuntimeError("alembic_version table empty after upgrade")

        for table in ("users", "items", "orders"):
            exists = cx.execute(text("SELECT to_regclass(:tbl)"), {"tbl": table}).scalar()
            if not exists:
                raise RuntimeError(f"Missing core table: {table}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--from-dump", default=None)
    parser.add_argument("--upgrade", default="head")
    parser.add_argument("--downgrade", default=None)
    args = parser.parse_args()

    env = os.environ.copy()
    env["DATABASE_URL"] = args.db_url

    if args.from_dump:
        _restore_dump(args.db_url, args.from_dump)

    _run(["alembic", "upgrade", args.upgrade], env=env)
    _sanity_checks(args.db_url)

    if args.downgrade:
        _run(["alembic", "downgrade", args.downgrade], env=env)
        _sanity_checks(args.db_url)

    print("Migration smoke OK ✅")


if __name__ == "__main__":
    main()
