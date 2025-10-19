from __future__ import annotations

def __getattr__(name: str):
    # "from erp.db import db" → hand back the models’ SQLAlchemy instance
    if name == "db":
        from erp.models import db as _db
        return _db
    # Anything else (User, Inventory, …) forward to erp.models lazily
    from erp import models as _models
    return getattr(_models, name)

__all__ = ["db"]


