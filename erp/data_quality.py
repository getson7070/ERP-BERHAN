"""Data hygiene helpers."""
from datetime import datetime
from typing import Iterable
import re
import logging
import sqlite3
from sqlalchemy.exc import DBAPIError
from db import get_db

logger = logging.getLogger(__name__)

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str) -> None:
    """Ensure table or column names are safe to interpolate."""
    if not _IDENT_RE.match(name):
        raise ValueError("Invalid identifier: %s" % name)


def deduplicate(table: str, key_fields: Iterable[str]) -> int:
    """Remove duplicate rows based on key fields.
    Returns number of rows deleted.
    """
    _validate_identifier(table)
    for field in key_fields:
        _validate_identifier(field)
    conn = get_db(); cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")  # nosec B608
    before = cur.fetchone()[0]
    conditions = ' AND '.join([f'a.{f}=b.{f}' for f in key_fields])
    try:
        query = (
            f"DELETE FROM {table} a USING {table} b "
            f"WHERE a.ctid < b.ctid AND {conditions}"
        )  # nosec
        cur.execute(query)
    except (DBAPIError, sqlite3.DatabaseError) as exc:
        logger.warning("Falling back to rowid dedupe for %s: %s", table, exc)
        group = ', '.join(key_fields)
        query = (
            f"DELETE FROM {table} "
            "WHERE rowid NOT IN ("
            f"SELECT MIN(rowid) FROM {table} GROUP BY {group})"
        )  # nosec
        cur.execute(query)
    conn.commit()
    cur.execute(f"SELECT COUNT(*) FROM {table}")  # nosec
    after = cur.fetchone()[0]
    cur.close(); conn.close()
    return before - after


def detect_conflict(existing_ts: datetime, new_ts: datetime) -> bool:
    """Return True if incoming timestamp is older than existing."""
    return new_ts < existing_ts
