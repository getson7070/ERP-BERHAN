# erp/__init__.py
import eventlet
eventlet.monkey_patch()

from .app import create_app
__all__ = ["create_app"]
