#!/usr/bin/env python
"""Report sequential scan statistics to guide index creation.

Connects to the database defined by ``DATABASE_URL`` and prints
``pg_stat_user_tables`` data. Fails if any table has sequential scans but
no index usage.
"""
import csv
import os
import sys

import psycopg2


def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL not set")
    query = (
        "SELECT relname, seq_scan, idx_scan "
        "FROM pg_stat_user_tables ORDER BY seq_scan DESC"
    )
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    writer = csv.writer(sys.stdout)
    writer.writerow(["table", "seq_scan", "idx_scan"])
    writer.writerows(rows)
    missing = [r[0] for r in rows if r[1] > 0 and r[2] == 0]
    if missing:
        print("tables needing indexes: " + ", ".join(missing), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
