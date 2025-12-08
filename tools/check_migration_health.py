"""Preflight guard to detect migration conflicts before deployment.

This helper is intentionally lightweight so it can run in CI or locally
before applying migrations. It surfaces the most common sources of schema
drift we have encountered in this repo:

* Multiple migration roots (`alembic/` *and* `migrations/`)
* Alembic pointing at the wrong script location
* Divergent heads inside the active migration tree

It does **not** apply migrations; it only validates configuration and
structure. Exit code `0` means the migration layout looks healthy; non-zero
means a human should inspect the reported items before proceeding.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[1]


def _format_paths(paths: list[Path]) -> str:
    return ", ".join(str(p) for p in paths)


def main() -> int:
    problems: List[str] = []

    # 1) Detect multiple migration roots. The canonical path is migrations/.
    migration_roots = [p for p in (ROOT / "migrations", ROOT / "alembic") if p.exists()]
    if len(migration_roots) > 1:
        problems.append(
            "Detected more than one migration root (expected only migrations/): "
            f"{_format_paths(migration_roots)}"
        )

    # 2) Validate Alembic configuration points to the canonical migrations/ location.
    alembic_ini = ROOT / "alembic.ini"
    if alembic_ini.exists():
        cfg = Config(str(alembic_ini))
        script_location = Path(cfg.get_main_option("script_location", "")).resolve()
        expected_location = (ROOT / "migrations").resolve()
        if script_location != expected_location:
            problems.append(
                f"Alembic script_location points to {script_location}, expected {expected_location}"
            )

        try:
            script_dir = ScriptDirectory.from_config(cfg)
            heads = script_dir.get_heads()
            if len(heads) > 1:
                head_list = ", ".join(heads)
                problems.append(
                    "Multiple Alembic heads detected ({}): {}. "
                    "Run `alembic merge` or apply the latest merge revision "
                    "(e.g., 20251212100000) before deploying.".format(
                        len(heads), head_list
                    )
                )
        except Exception as exc:  # pragma: no cover - defensive guard for misconfigured environments
            problems.append(f"Could not inspect migration heads: {exc}")
    else:
        problems.append("alembic.ini not found; cannot validate migration setup.")

    if problems:
        for item in problems:
            print(f"[migration-check] {item}")
        return 1

    print("[migration-check] OK: single migration root, correct script_location, single head.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
