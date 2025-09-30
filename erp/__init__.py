# erp/__init__.py
# Keep package namespace minimal to avoid circular imports.
# Access create_app/socketio via `from erp.app import create_app, socketio`.
from .extensions import db, limiter, oauth, jwt, cache, compress, csrf, babel  # noqa: F401
from .app import create_app, socketio  # noqa: F401
from .constants import AUDIT_CHAIN_BROKEN  # noqa: F401
