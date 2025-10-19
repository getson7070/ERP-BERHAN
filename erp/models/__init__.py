# erp/models/__init__.py
# Import the shared SQLAlchemy instance
from erp.db import db  # noqa: F401

# Tolerant imports: only bring in modules that actually exist
_modules = [
    "user",
    "employee",
    "finance",
    "idempotency",
    "integration",
    "recall",
    "user_dashboard",
    "inventory",
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

from .organization import *  # noqa: F401,F403

from .user import *  # noqa: F401,F403

from .invoice import *  # noqa: F401,F403

from .recruitment import *  # noqa: F401,F403

from .performance_review import *  # noqa: F401,F403
