# db.py
from __future__ import annotations
import os, sqlite3, threading
from contextlib import contextmanager
from sqlalchemy.sql.elements import TextClause  # NEW

_DB_LOCAL = threading.local()

class _DBWrapper:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self.row_factory = conn.row_factory

    def cursor(self): return self._conn.cursor()
    def commit(self): return self._conn.commit()
    def close(self):  return self._conn.close()

    def execute(self, *a, **k):
        # Allow sqlalchemy.text("...") as first arg
        if a and isinstance(a[0], TextClause):
            a = (a[0].text, *a[1:])
        return self._conn.execute(*a, **k)

def _open_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def get_db() -> _DBWrapper:
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        path = db_url.replace("sqlite:///", "")
    else:
        path = os.getenv("DATABASE_PATH", ":memory:")
    if not hasattr(_DB_LOCAL, "conn") or _DB_LOCAL.conn is None:
        _DB_LOCAL.conn = _open_db(path)
    return _DBWrapper(_DB_LOCAL.conn)
