"""Module: socket.py — audit-added docstring. Refine with precise purpose when convenient."""

try:
    from flask_socketio import SocketIO
    socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")
except Exception:
    socketio = None

