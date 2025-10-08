#!/usr/bin/env python
"""Report sequential scan statistics to guide index creation.

Connects to the database defined by ``DATABASE_URL`` and prints
``pg_stat_user_tables`` data. Fails if any table has sequential scans but
no index usage. Optionally writes a JSON report for dashboard automation.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import psycopg2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional path to write a JSON report for dashboards or ticketing",
    )
    return parser.parse_args()


def fetch_stats(dsn: str) -> Sequence[tuple[str, int, int]]:
    query = (
        "SELECT relname, seq_scan, idx_scan "
        "FROM pg_stat_user_tables ORDER BY seq_scan DESC"
    )
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return [(name, int(seq), int(idx)) for name, seq, idx in rows]


def write_csv(rows: Sequence[tuple[str, int, int]]) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["table", "seq_scan", "idx_scan"])
    writer.writerows(rows)


def write_report(rows: Sequence[tuple[str, int, int]], path: Path) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tables": [
            {
                "table": name,
                "seq_scan": seq,
                "idx_scan": idx,
                "needs_index": seq > 0 and idx == 0,
            }
            for name, seq, idx in rows
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL not set")

    rows = fetch_stats(dsn)
    write_csv(rows)

    if args.report:
        write_report(rows, args.report)

    missing = [name for name, seq, idx in rows if seq > 0 and idx == 0]
    if missing:
        print("tables needing indexes: " + ", ".join(missing), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
