"""Run a disaster-recovery restore drill.

This helper ensures the repository root is on ``sys.path`` so the
``backup`` module can be imported even when the script is executed from an
external working directory (as is done in tests). It always writes a
``dr-drill.csv`` file capturing a success flag and any error message so the
calling environment can record drill outcomes without leaking stack traces.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    status = "ok"
    detail = ""
    try:
        from backup import perform_restore_drill

        perform_restore_drill()
    except Exception as exc:  # pragma: no cover - best effort logging
        status = "error"
        detail = str(exc)

    with open("dr-drill.csv", "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["status", "detail"])
        writer.writerow([status, detail])


if __name__ == "__main__":
    main()


