"""
Central DB module for SQLAlchemy and models.

Re-exports commonly-used models so tests/blueprints can import consistently.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Core models (existing)
from .models.user import User
from .models.org import Organization

# Re-export for convenience
try:
    from .models.inventory import Inventory
except ImportError:
    Inventory = None

try:
    from .models.user_dashboard import UserDashboard
except ImportError:
    UserDashboard = None

__all__ = [
    "db",
    "User",
    "Organization",
    "Inventory",
    "UserDashboard",
]
