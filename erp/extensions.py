# erp/extensions.py
from __future__ import annotations

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Global limiter object used across the app.
# storage_uri can be swapped to redis:// for multi-instance deployments.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

def init_extensions(app: Flask) -> None:
    """
    Call this exactly once in your create_app() to wire extensions.
    """
    limiter.init_app(app)
