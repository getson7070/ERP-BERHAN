"""Data hygiene helpers."""

from datetime import datetime
from typing import Iterable
import re
import logging
from sqlalchemy import MetaData, Table, delete, func, literal_column, select
from sqlalchemy.exc import DBAPIError
from db import get_engine

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

    engine = get_engine()
    metadata = MetaData()
    t = Table(table, metadata, autoload_with=engine)

    with engine.begin() as conn:
        before = conn.execute(select(func.count()).select_from(t)).scalar_one()
        if engine.dialect.name == "postgresql":
            a = t.alias("a")
            b = t.alias("b")
            conditions = [a.c[f] == b.c[f] for f in key_fields]
            a_ctid = literal_column("ctid"); a_ctid.table = a
            b_ctid = literal_column("ctid"); b_ctid.table = b
            try:
                stmt = delete(a).where(a_ctid < b_ctid, *conditions)
                conn.execute(stmt)
            except DBAPIError as exc:
                logger.warning("Falling back to rowid dedupe for %s: %s", table, exc)
                rowid = literal_column("rowid")
                subq = (
                    select(func.min(rowid).label("min_rowid"), *[t.c[f] for f in key_fields])
                    .group_by(*[t.c[f] for f in key_fields])
                    .subquery()
                )
                stmt = delete(t).where(rowid.notin_(select(subq.c.min_rowid)))
                conn.execute(stmt)
        else:
            rowid = literal_column("rowid")
            subq = (
                select(func.min(rowid).label("min_rowid"), *[t.c[f] for f in key_fields])
                .group_by(*[t.c[f] for f in key_fields])
                .subquery()
            )
            stmt = delete(t).where(rowid.notin_(select(subq.c.min_rowid)))
            conn.execute(stmt)
        after = conn.execute(select(func.count()).select_from(t)).scalar_one()
    return before - after


def detect_conflict(existing_ts: datetime, new_ts: datetime) -> bool:
    """Return True if incoming timestamp is older than existing."""
    return new_ts < existing_ts
