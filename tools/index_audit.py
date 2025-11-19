"""Verify that critical database indexes exist and remain healthy."""
from __future__ import annotations

import argparse
import argparse
import os
from typing import Dict, Iterable

from sqlalchemy import create_engine, text

CRITICAL_INDEXES: Dict[str, tuple[str, ...]] = {
    "audit_logs": ("ix_audit_logs_org_action", "pk_audit_logs"),
    "finance_entries": ("ix_finance_entries_org_id", "ix_finance_entries_account"),
    "orders": ("ix_orders_organization_id",),
    "user_role_assignments": ("uq_user_role_assignments",),
}


def _resolve_database_url(cli_url: str | None) -> str:
    url = cli_url or os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not url:
        raise SystemExit("DATABASE_URL or SQLALCHEMY_DATABASE_URI must be set.")
    return url


def _existing_indexes(connection, table: str) -> set[str]:
    result = connection.execute(
        text(
            "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() AND tablename = :table"
        ),
        {"table": table},
    )
    return {row.indexname for row in result}


def _summarize_usage(connection, table: str) -> Iterable[tuple[str, float]]:
    stats = connection.execute(
        text(
            """
            SELECT indexrelname, idx_scan
            FROM pg_stat_user_indexes
            WHERE schemaname = current_schema() AND relname = :table
            ORDER BY idx_scan DESC
            """
        ),
        {"table": table},
    )
    for row in stats:
        yield row.indexrelname, float(row.idx_scan or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", dest="database_url")
    args = parser.parse_args()

    engine = create_engine(_resolve_database_url(args.database_url))

    missing: list[str] = []
    cold_indexes: list[str] = []

    with engine.begin() as conn:
        for table, expected_indexes in CRITICAL_INDEXES.items():
            present = _existing_indexes(conn, table)
            for index_name in expected_indexes:
                if index_name not in present:
                    missing.append(f"{table}.{index_name}")

            for index_name, scan_count in _summarize_usage(conn, table):
                if scan_count == 0 and index_name in expected_indexes:
                    cold_indexes.append(f"{table}.{index_name}")

    if missing:
        raise SystemExit(
            "Missing indexes: "
            + ", ".join(missing)
            + ". Run Alembic migrations or create the indexes manually before continuing."
        )

    if cold_indexes:
        print("WARN: Indexes exist but are unused — investigate query plans:")
        for entry in cold_indexes:
            print("  -", entry)

    print("All critical indexes are present.")


if __name__ == "__main__":
    main()
