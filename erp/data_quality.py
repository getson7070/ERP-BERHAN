"""Data hygiene helpers."""
from datetime import datetime
from typing import Iterable, Tuple
from db import get_db


def deduplicate(table: str, key_fields: Iterable[str]) -> int:
    """Remove duplicate rows based on key fields.
    Returns number of rows deleted.
    """
    conn = get_db(); cur = conn.cursor()
    conditions = ' AND '.join([f'a.{f}=b.{f}' for f in key_fields])
    try:
        query = f"""
            DELETE FROM {table} a USING {table} b
            WHERE a.ctid < b.ctid AND {conditions}
        """
        cur.execute(query)
    except Exception:
        group = ', '.join(key_fields)
        query = f"""
            DELETE FROM {table}
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM {table} GROUP BY {group}
            )
        """
        cur.execute(query)
    deleted = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    return deleted


def detect_conflict(existing_ts: datetime, new_ts: datetime) -> bool:
    """Return True if incoming timestamp is older than existing."""
    return new_ts < existing_ts
