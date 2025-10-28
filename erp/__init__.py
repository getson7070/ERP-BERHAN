"""ERP package initializer with zero side-effects."""
__all__ = ["create_app", "socketio"]
from .app import create_app
from .socket import socketio

