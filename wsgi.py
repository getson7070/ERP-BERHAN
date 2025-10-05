# wsgi.py
import os

# IMPORTANT: eventlet must monkey_patch BEFORE importing anything else that uses stdlib sockets/locks.
import eventlet
eventlet.monkey_patch()

from erp.app import create_app
from erp.extensions import socketio

app = create_app()

if __name__ == "__main__":
    # local dev
    port = int(os.getenv("PORT", "5000"))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
