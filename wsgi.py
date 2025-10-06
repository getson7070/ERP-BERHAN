# wsgi.py
import os
import eventlet
eventlet.monkey_patch()  # must happen before importing app/extensions

from erp.app import create_app
from erp.extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
