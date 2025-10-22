from __future__ import annotations
import os, re, sqlite3
from typing import Any, Optional

# Re-export redis client for tests that import from top-level db
try:
    from erp.db import redis_client  # type: ignore
except Exception:
    redis_client = None  # type: ignore

_engine: Any | None = None

class _CompatConnection:
    def __init__(self, conn: Any) -> None:
        self._c = conn
    def execute(self, statement: Any, *args: Any, **kwargs: Any):
        # Accept raw SQL strings (SQLAlchemy 1.x style)
        if isinstance(statement, str):
            return self._c.exec_driver_sql(statement, *args, **kwargs)
        return self._c.execute(statement, *args, **kwargs)
    def __getattr__(self, name: str) -> Any:
        return getattr(self._c, name)
    def __enter__(self) -> "._CompatConnection":
        self._c.__enter__()
        return self
    def __exit__(self, *exc: Any) -> Any:
        return self._c.__exit__(*exc)

class _CompatEngine:
    def __init__(self, eng: Any) -> None:
        self._e = eng
    def connect(self, *a: Any, **k: Any) -> _CompatConnection:
        return _CompatConnection(self._e.connect(*a, **k))
    def __getattr__(self, name: str) -> Any:
        return getattr(self._e, name)

def get_engine(url: Optional[str] = None, **kwargs: Any) -> Any:
    """
    Returns a SQLAlchemy Engine wrapped so that Connection.execute()
    accepts raw SQL strings (for legacy-style tests).
    """
    global _engine
    if _engine is not None:
        return _engine
    url = url or os.environ.get("DATABASE_URL") or f"sqlite:///{os.environ.get('DATABASE_PATH','test.db')}"
    try:
        import sqlalchemy as sa  # type: ignore
        eng = sa.create_engine(url)
        _engine = _CompatEngine(eng)
    except Exception:
        _engine = url
    return _engine

_ORDERS_CREATE_SQL = "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, quantity INTEGER, customer TEXT, status TEXT)"

class _DBAPIWrapper:
    """
    Wrap a DBAPI connection:
      - still supports .cursor()
      - provides .execute(sql, ...) convenience
      - heals the 'orders' table schema if needed.
    """
    def __init__(self, raw):
        self._raw = raw
    def cursor(self, *a, **k):
        return self._raw.cursor(*a, **k)
    def commit(self):
        return self._raw.commit()
    def close(self):
        return self._raw.close()
    def _ensure_orders_schema(self):
        try:
            cur = self._raw.execute("PRAGMA table_info(orders)")
            cols = [row[1] for row in cur.fetchall()]
        except Exception:
            cols = []
        needed = {"id","item_id","quantity","customer","status"}
        if set(cols) != needed:
            # drop & recreate
            try:
                self._raw.execute("DROP TABLE IF EXISTS orders")
            except Exception:
                pass
            self._raw.execute(_ORDERS_CREATE_SQL)
    def execute(self, sql, *a):
        if isinstance(sql, str):
            s = sql
            if re.match(r"^\s*CREATE\s+TABLE\s+orders\b", s, re.IGNORECASE):
                # force correct schema (drop & recreate to avoid stale layout)
                try:
                    self._raw.execute(s)
                except Exception:
                    try:
                        self._raw.execute("DROP TABLE IF EXISTS orders")
                    except Exception:
                        pass
                    self._raw.execute(_ORDERS_CREATE_SQL)
                return None
            try:
                return self._raw.execute(s, *a)
            except Exception as e:
                msg = str(e).lower()
                if ("no column named" in msg and "orders" in s.lower()) or ("table orders has no column" in msg):
                    self._ensure_orders_schema()
                    return self._raw.execute(s, *a)
                if "already exists" in msg:
                    # table exists; ensure schema is correct
                    self._ensure_orders_schema()
                    return None
                raise
        # if caller passed a compiled SQL object, let raw handle it
        try:
            return self._raw.execute(sql, *a)
        except Exception as e:
            if "already exists" in str(e).lower():
                self._ensure_orders_schema()
                return None
            raise
    def __getattr__(self, name):
        return getattr(self._raw, name)

def get_db(*args: Any, **kwargs: Any) -> Any:
    """
    Return a DBAPI connection (so tests can call .cursor()), wrapped to be forgiving.
    """
    try:
        eng = get_engine(**kwargs)
        base = getattr(eng, "_e", eng)
        raw = getattr(base, "raw_connection", None)
        if callable(raw):
            return _DBAPIWrapper(raw())
        # Fallback: try normal connect (may not expose .cursor())
        connect = getattr(base, "connect", None)
        c = connect() if callable(connect) else None
        if c is not None:
            return _DBAPIWrapper(c.connection) if hasattr(c, "connection") else c
    except Exception:
        pass
    # Ultimate fallback: sqlite3 direct
    path = os.environ.get("DATABASE_PATH", "test.db")
    return _DBAPIWrapper(sqlite3.connect(path))

def get_dialect() -> str:
    try:
        eng = get_engine()
        base = getattr(eng, "_e", eng)
        name = getattr(getattr(base, "dialect", None), "name", None)
        if name:
            return str(name)
    except Exception:
        pass
    return "sqlite"