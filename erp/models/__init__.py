# erp/models/__init__.py
# Re-export models here so `from erp.models import X` works everywhere.
from erp.extensions import db
from .user import User, DeviceAuthorization, DataLineage  # keep existing models
from .user_dashboard import UserDashboard  # ensure dashboard feature never breaks imports

__all__ = [
    "db",
    "User",
    "DeviceAuthorization",
    "DataLineage",
    "UserDashboard",
]
