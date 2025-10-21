"""
Thin export shim so tests can import `db` and common models from `erp.db`
without requiring a live database. If Flask-SQLAlchemy is available, a
SQLAlchemy instance is exposed; otherwise a no-op stub with a `.session`
that implements add/commit/rollback.
"""
from __future__ import annotations

# Optional: attempt to provide a real SQLAlchemy handle if available.
try:
    from flask_sqlalchemy import SQLAlchemy  # type: ignore
    db = SQLAlchemy(session_options={"autoflush": False})
except Exception:  # pragma: no cover
    class _DummySession:
        def add(self, *a, **k): pass
        def add_all(self, *a, **k): pass
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass

    class _DummyDB:
        def __init__(self):
            self.session = _DummySession()
        def create_all(self): pass
        def drop_all(self): pass

    db = _DummyDB()

# Re-export models so tests can do:
#   from erp.db import db, User, Inventory, UserDashboard
try:
    from .models import User, Inventory, UserDashboard  # type: ignore
except Exception:  # pragma: no cover
    User = Inventory = UserDashboard = None  # type: ignore

__all__ = ["db", "User", "Inventory", "UserDashboard"]
