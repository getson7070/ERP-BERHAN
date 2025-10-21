from __future__ import annotations

# Use the app-wide SQLAlchemy if available; otherwise fall back (eg. for isolated tests/CLI)
try:
    from ..extensions import db  # type: ignore
except Exception:  # pragma: no cover
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

__all__ = ["db", 'Inventory', 'User', 'Role']

# Eagerly import only modules known to be safe at import time.  (Exclude "inventory".)
_modules = [
    "user",
    "employee",
    "finance",
    "idempotency",
    "integration",
    "recall",
    "user_dashboard",
    "organization",
    "invoice",
    "recruitment",
    "performance_review",
    "order",
    "role",
]

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

# Lazy export for inventory classes to avoid import-time side-effects.
# Back-compat: accept several possible class names.
_BACKCOMPAT_ITEM_NAMES = ("Item", "InventoryItem", "Product", "StockItem")

def __getattr__(name: str):
    if name in _BACKCOMPAT_ITEM_NAMES:
        try:
            from . import inventory as _inv  # import only when requested
        except Exception as e:
            raise AttributeError(
                f"'erp.models' cannot provide {name!r}: inventory failed to import"
            ) from e
        # Cache whichever names exist so subsequent access is direct
        for _cand in _BACKCOMPAT_ITEM_NAMES:
            if hasattr(_inv, _cand):
                _obj = getattr(_inv, _cand)
                globals()[_cand] = _obj
                if _cand not in __all__:
                    __all__.append(_cand)
        if name in globals():
            return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
try:
    from .user import User
except Exception:  # pragma: no cover - import fallback for tests
    User = None  # type: ignore
try:
    from .role import Role
except Exception:  # pragma: no cover - import fallback for tests
    Role = None  # type: ignore
