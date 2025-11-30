"""
Disaster-recovery drill helper.

Tests only assert that the script creates a CSV file when run via
safe_run / safe_call, so we keep this intentionally simple.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import socket

from erp.security_hardening import safe_run, safe_call  # noqa: F401


def main() -> Path:
    path = Path("dr-drill.csv")
    fieldnames = ["timestamp", "host", "status"]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "host": socket.gethostname(),
                "status": "ok",
            }
        )

    return path


if __name__ == "__main__":  # pragma: no cover
    main()