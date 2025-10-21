#!/usr/bin/env python
"""Fail if a query would trigger a sequential scan.

Pass a SQL query as the first argument. Connection string taken from
DATABASE_URL env variable.
"""
import os
import sys

import psycopg2


def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL not set")
    if len(sys.argv) < 2:
        raise SystemExit("usage: check_indexes.py <SQL>")
    query = sys.argv[1]
    params = tuple(sys.argv[2:])
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("EXPLAIN " + query, params)
            plan_rows = cur.fetchall()
    plan = "\n".join(r[0] for r in plan_rows)
    print(plan)
    if "Seq Scan" in plan:
        raise SystemExit(1)


if __name__ == "__main__":
    main()


