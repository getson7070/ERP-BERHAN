"""ORM compatibility layer for legacy imports.

Historically the SQLAlchemy instance lived in ``erp.db``; newer code uses
``erp.extensions`` to keep all Flask extensions together.  To remain
backwards compatible we simply re-export the shared ``db`` instance here
and lazily expose the ``User`` model so tests that import
``from erp.db import db, User`` continue to work.
"""

from __future__ import annotations

from typing import Any

from .extensions import db as db  # re-exported SQLAlchemy handle

try:  # pragma: no cover - import may fail in minimal deployments
    from erp.models.user import User  # type: ignore
except Exception:  # pragma: no cover - fallback when models unavailable
    User = Any  # type: ignore[misc,assignment]

__all__ = ["db", "User"]

