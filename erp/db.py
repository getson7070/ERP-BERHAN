from __future__ import annotations
# Thin re-export shim so tests can: from erp.db import db, User, Inventory, ...
from erp import models as _models

# Re-export the SQLAlchemy instance
db = _models.db

# Forward any attribute lookups to erp.models (User, Role, Inventory, etc.)
def __getattr__(name: str):
    return getattr(_models, name)

# Best-effort __all__
try:
    _all = list(getattr(_models, "__all__", []))
except Exception:
    _all = []
__all__ = ["db", *_all]
