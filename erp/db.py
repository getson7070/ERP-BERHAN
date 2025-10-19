from __future__ import annotations

# Lazy re-export shim so tests can: from erp.db import db, User, Inventory, ...
def __getattr__(name: str):
    from erp import models as _models
    if name == "db":
        return _models.db
    return getattr(_models, name)

# Provide an object named "db" that forwards attributes like .Model, .session, ...
class _DBProxy:
    def __getattr__(self, attr):
        from erp import models as _models
        return getattr(_models.db, attr)
db = _DBProxy()

__all__ = ["db"]
