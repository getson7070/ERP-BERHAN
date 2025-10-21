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




# --- AUTOAPPEND (safe) ---
try:
    from .models import Inventory, User, Role  # type: ignore
    __all__ = [n for n in ("Inventory","User","Role") if n in globals()]
except Exception:
    pass


# --- autopatch: re-export common models for test imports ---
try:
    from .models.inventory import Inventory  # type: ignore
except Exception:
    try:
        from erp.models.inventory import Inventory  # type: ignore
    except Exception:
        Inventory = None  # type: ignore

try:
    from .models.user import User  # type: ignore
except Exception:
    try:
        from erp.models.user import User  # type: ignore
    except Exception:
        User = None  # type: ignore

try:
    from .models.role import Role  # type: ignore
except Exception:
    try:
        from erp.models.role import Role  # type: ignore
    except Exception:
        Role = None  # type: ignore
# --- end autopatch ---
