"""
Central DB module for SQLAlchemy and models.

Re-exports commonly-used models so tests/blueprints can import consistently.
"""

from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy handle
db = SQLAlchemy()

# Core models (existing) – imported defensively so that a missing
# optional module does not break `from erp import db`.
try:
    from .models.user import User  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    User = None  # type: ignore[assignment]

try:
    # Correct file is `organization.py`, not `org.py`
    from .models.organization import Organization  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    Organization = None  # type: ignore[assignment]

# Optional convenience re-exports
try:
    from .models.inventory import Inventory  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    Inventory = None  # type: ignore[assignment]

try:
    from .models.user_dashboard import UserDashboard  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    UserDashboard = None  # type: ignore[assignment]


__all__ = [
    "db",
    "User",
    "Organization",
    "Inventory",
    "UserDashboard",
]
