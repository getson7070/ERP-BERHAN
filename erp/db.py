from flask_sqlalchemy import SQLAlchemy  # type: ignore

# Single shared SQLAlchemy instance for the app
db = SQLAlchemy()

# Re-export models so tests can do: from erp.db import db, User, Inventory
try:
    from erp import models as _models  # noqa: E402
    # Copy public names into this module's globals
    if hasattr(_models, "__all__"):
        for _n in _models.__all__:
            globals()[_n] = getattr(_models, _n)
        __all__ = ["db"] + list(_models.__all__)
    else:
        __all__ = ["db"]
except Exception:  # pragma: no cover - models might import this before ready
    __all__ = ["db"]
