"""Data hygiene helpers."""

from datetime import datetime
from typing import Iterable
import re
from sqlalchemy import MetaData, Table, delete, func, literal_column, select
from db import get_engine

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str) -> None:
    """Ensure table or column names are safe to interpolate."""
    if not _IDENT_RE.match(name):
        raise ValueError("Invalid identifier: %s" % name)


def deduplicate(table: str, key_fields: Iterable[str]) -> int:
    """Remove duplicate rows based on key fields using window functions.

    Returns number of rows deleted.
    """
    _validate_identifier(table)
    for field in key_fields:
        _validate_identifier(field)

    engine = get_engine()
    metadata = MetaData()
    t = Table(table, metadata, autoload_with=engine)

    with engine.begin() as conn:
        before = conn.execute(select(func.count()).select_from(t)).scalar_one()

        pk_cols = list(t.primary_key.columns)
        if pk_cols:
            order_col = pk_cols[0]
        else:
            order_col = literal_column("rowid")
            order_col.table = t

        partition_cols = [t.c[f] for f in key_fields]
        rn = func.row_number().over(partition_by=partition_cols, order_by=order_col).label("rn")
        order_label = order_col.label("ord_col")
        subq = select(order_label, rn).subquery()
        stmt = delete(t).where(
            order_col.in_(select(subq.c.ord_col).where(subq.c.rn > 1))
        )
        conn.execute(stmt)

        after = conn.execute(select(func.count()).select_from(t)).scalar_one()
    return before - after


def detect_conflict(existing_ts: datetime, new_ts: datetime) -> bool:
    """Return True if incoming timestamp is older than existing."""
    return new_ts < existing_ts
