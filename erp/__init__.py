# erp/__init__.py
# Keep this file tiny. Do NOT define init_extensions here.
from .app import create_app

# (Optional) re-export extensions if you want easy imports elsewhere
from .extensions import db, migrate, cache, limiter, login_manager, mail, socketio, init_extensions  # noqa: F401

__all__ = ["create_app", "db", "migrate", "cache", "limiter", "login_manager", "mail", "socketio", "init_extensions"]
