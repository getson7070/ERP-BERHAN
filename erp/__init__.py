# erp/__init__.py
from .extensions import db, limiter, oauth, jwt, cache, compress, csrf, babel  # noqa: F401
from .app import create_app, socketio  # noqa: F401
