"""Automate backup and index verification drills in one run."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _run_step(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        dest="database_url",
        help="Optional override passed through to child commands.",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("logs/resilience-suite"),
        type=Path,
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = args.output_dir / f"resilience-{timestamp}.json"

    backup_cmd = [sys.executable, "tools/backup_drill.py", "--output-dir", str(args.output_dir / "backup")]
    if args.database_url:
        backup_cmd.extend(["--database-url", args.database_url])

    index_cmd = [sys.executable, "tools/index_audit.py"]
    if args.database_url:
        index_cmd.extend(["--database-url", args.database_url])

    report = {
        "generated_at": timestamp,
        "steps": [
            _run_step(backup_cmd),
            _run_step(index_cmd),
        ],
    }

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    failures = [step for step in report["steps"] if step["returncode"] != 0]
    if failures:
        raise SystemExit(
            "Resilience suite failed — inspect " + str(report_path)
        )
    print("Resilience suite complete:", report_path)


if __name__ == "__main__":
    main()
