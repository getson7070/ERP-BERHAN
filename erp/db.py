from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance for all models
db = SQLAlchemy()

# Re-export models so tests can do: from erp.db import db, User, Inventory, ...
try:
    from .models import *  # noqa: F401,F403
except Exception:
    pass
