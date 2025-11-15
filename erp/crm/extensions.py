# -*- coding: utf-8 -*-
"""
Legacy shim for old imports like:
  from erp.crm.extensions import db, migrate, login_manager, csrf
Prefer importing from `erp.extensions` (db, etc.) and `from erp import csrf` going forward.
"""

# Canonical shared handles (db, etc.)
try:
    from erp.extensions import db
except Exception:  # pragma: no cover
    db = None

# Optional Migrate handle
try:
    from flask_migrate import Migrate
    migrate = Migrate()
except Exception:  # pragma: no cover
    migrate = None

# Optional LoginManager handle
try:
    from flask_login import LoginManager
    login_manager = LoginManager()
except Exception:  # pragma: no cover
    login_manager = None

# Export the CSRFProtect instance created at module level in erp/__init__.py
try:
    from erp import csrf
except Exception:  # pragma: no cover
    csrf = None