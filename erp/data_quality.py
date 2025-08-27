"""Data hygiene helpers."""
from datetime import datetime
import re
from typing import Iterable

from db import get_db


def deduplicate(table: str, key_fields: Iterable[str]) -> int:
    """Remove duplicate rows based on *key_fields*.

    The ``table`` and column names are validated to contain only simple
    identifiers before being injected into a statement using SQLAlchemy's
    ``bindparam`` with ``literal_execute`` to avoid SQL injection risks.
    Returns the number of rows deleted.
    """

    identifier = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    if not identifier.match(table) or any(not identifier.match(f) for f in key_fields):
        raise ValueError("Invalid identifier supplied")

    conn = get_db(); cur = conn.cursor()
    conditions = " AND ".join([f"a.{f}=b.{f}" for f in key_fields])
    dialect = getattr(conn, "_dialect", None)
    if dialect and dialect.name == "sqlite":
        group = ", ".join(key_fields)
        query = f"""
            DELETE FROM {table}
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM {table} GROUP BY {group}
            )
        """  # nosec B608
        cur.execute(query)
    else:
        try:
            query = f"""
                DELETE FROM {table} a USING {table} b
                WHERE a.ctid < b.ctid AND {conditions}
            """  # nosec B608
            cur.execute(query)
        except Exception:
            group = ", ".join(key_fields)
            query = f"""
                DELETE FROM {table}
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) FROM {table} GROUP BY {group}
                )
            """  # nosec B608
            cur.execute(query)
    deleted = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    return deleted


def detect_conflict(existing_ts: datetime, new_ts: datetime) -> bool:
    """Return True if incoming timestamp is older than existing."""
    return new_ts < existing_ts
