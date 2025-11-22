#!/usr/bin/env python
"""Ensure every Alembic revision has a matching doc in docs/migrations."""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIGRATIONS = REPO / "migrations" / "versions"
DOCS = REPO / "docs" / "migrations"


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []

    for migration in MIGRATIONS.glob("*.py"):
        text = migration.read_text(encoding="utf-8")
        match = re.search(r"revision\s*=\s*['\"]([a-f0-9]+)['\"]", text)
        if not match:
            continue
        rev = match.group(1)
        doc_path = DOCS / f"{rev}.md"
        if not doc_path.exists():
            missing.append(rev)

    if missing:
        if os.getenv("ALLOW_MISSING_MIGRATION_DOCS") == "1":
            print("Missing migration docs (allowed in this run):", missing)
        else:
            print("Missing migration docs:", missing)
            raise SystemExit(1)

    print("All migration docs OK ✅")


if __name__ == "__main__":
    main()
