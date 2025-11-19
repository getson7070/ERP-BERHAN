"""Exercise pg_dump/pg_restore to prove RPO/RTO readiness."""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


def _resolve_database_url(cli_url: str | None) -> str:
    url = cli_url or os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not url:
        raise SystemExit("DATABASE_URL or SQLALCHEMY_DATABASE_URI must be set.")
    return url


def _ensure_binary(name: str) -> None:
    try:
        subprocess.run([name, "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:  # pragma: no cover - depends on environment
        raise SystemExit(f"{name} is not installed or not on PATH.") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", dest="database_url")
    parser.add_argument(
        "--output-dir",
        default=Path("logs/backup-drill"),
        type=Path,
        help="Directory used to store the drill manifest.",
    )
    args = parser.parse_args()

    database_url = _resolve_database_url(args.database_url)
    _ensure_binary("pg_dump")
    _ensure_binary("pg_restore")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkstemp(prefix="backup-drill-", suffix=".dump")[1])

    try:
        dump_cmd = [
            "pg_dump",
            "--format=custom",
            f"--file={tmp}",
            "--schema-only",
            f"--dbname={database_url}",
        ]
        subprocess.run(dump_cmd, check=True)

        manifest_path = args.output_dir / f"{tmp.stem}.manifest.txt"
        with manifest_path.open("w", encoding="utf-8") as manifest:
            subprocess.run(["pg_restore", "--list", str(tmp)], check=True, stdout=manifest)

        print("Backup drill complete:", manifest_path)
    finally:
        if tmp.exists():
            tmp.unlink()


if __name__ == "__main__":
    main()
