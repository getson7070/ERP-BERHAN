# erp/models/__init__.py
# Re-export models here so `from erp.models import X` works everywhere.
from erp.extensions import db
from .user import User, DeviceAuthorization, DataLineage  # existing models
from .user_dashboard import UserDashboard                  # existing model
from .employee import Employee                             # NEW

__all__ = [
    "db",
    "User",
    "DeviceAuthorization",
    "DataLineage",
    "UserDashboard",
    "Employee",
]
