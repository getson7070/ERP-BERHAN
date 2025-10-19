from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance
db = SQLAlchemy()

# Lazily expose model names so tests can do:
#   from erp.db import db, User, Inventory, ...
# without creating an import cycle.
def __getattr__(name: str):
    from . import models as _m
    if hasattr(_m, name):
        return getattr(_m, name)
    raise AttributeError(name)

__all__ = ["db"]  # model symbols are resolved lazily via __getattr__
