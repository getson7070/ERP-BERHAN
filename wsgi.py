# wsgi.py — very first lines
import eventlet
eventlet.monkey_patch(all=True)
# app/__init__.py
from flask_socketio import SocketIO
socketio = SocketIO(async_mode="eventlet")  # **no** message_queue unless configured
import os
from app import create_app  # or however your factory is named
app = create_app()
"""WSGI entry point for the BERHAN ERP application."""

from erp import create_app

app = create_app()
