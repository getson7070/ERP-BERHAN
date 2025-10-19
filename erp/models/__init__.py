<<<<<<< HEAD
# erp/models/__init__.py

# Use the shared SQLAlchemy instance (do NOT create a new one here)
from ..extensions import db

# Tolerant imports: exclude 'inventory' to avoid import-time side-effects
=======
﻿from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# Tolerant imports: only bring in modules that actually exist
>>>>>>> 6232ca4 (Renormalize line endings)
_modules = [
    "user",
    "employee",
    "finance",
    "idempotency",
    "integration",
    "recall",
    "user_dashboard",
    # "inventory",   # <-- intentionally excluded
]

__all__ = []
for _m in _modules:
    try:
        _mod = __import__(f"{__name__}.{_m}", fromlist=["*"])
    except Exception:
        continue
    for _k, _v in _mod.__dict__.items():
        if _k.startswith("_"):
            continue
        globals()[_k] = _v
        __all__.append(_k)

from .organization import *          # noqa: F401,F403
from .user import *                  # noqa: F401,F403
from .invoice import *               # noqa: F401,F403
from .recruitment import *           # noqa: F401,F403
from .performance_review import *    # noqa: F401,F403
# from .inventory import *           # <-- DISABLED on purpose
from .order import *                 # noqa: F401,F403
from .role import *                  # noqa: F401,F403
from .user_dashboard import *        # noqa: F401,F403

<<<<<<< HEAD
# ---- Safe, back-compat export for Item (no star-imports, no side-effects) ----
try:
    from . import inventory as _inv  # import module only
    for _name in ("Item", "InventoryItem", "Product", "StockItem"):
        if hasattr(_inv, _name):
            Item = getattr(_inv, _name)
            __all__.append("Item")
            break
    else:
        Item = None  # tolerate in minimal/test environments
except Exception:
    Item = None
=======




>>>>>>> 6232ca4 (Renormalize line endings)
