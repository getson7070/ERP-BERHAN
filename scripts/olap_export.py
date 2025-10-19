"""Nightly export of fact tables to an OLAP store.

This script extracts materialized KPI tables and pushes them to an
external warehouse (e.g., TimescaleDB or ClickHouse). The implementation
below writes to a temporary CSV file for demonstration and increments a
Prometheus counter so CI can assert successful exports.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from db import get_db
from erp import OLAP_EXPORT_SUCCESS
from sqlalchemy import text


def fetch_kpi_sales() -> Iterable[tuple[int, float]]:
    """Yield kpi_sales rows as (org_id, total)."""
    conn = get_db()
    for row in conn.execute(text("SELECT org_id, total FROM kpi_sales")):
        yield row


def export_to_csv(rows: Iterable[tuple[int, float]], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["org_id", "total", "exported_at"])
        now = datetime.now(UTC).isoformat()
        for org_id, total in rows:
            writer.writerow([org_id, total, now])


def main() -> Path:
    """Run the export and return the CSV path."""
    rows = list(fetch_kpi_sales())
    dest = Path("exports/olap_kpi_sales.csv")
    export_to_csv(rows, dest)
    OLAP_EXPORT_SUCCESS.inc()
    return dest


if __name__ == "__main__":
    path = main()
    print(f"Exported to {path}")


