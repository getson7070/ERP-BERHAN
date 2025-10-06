# wsgi.py
import eventlet
eventlet.monkey_patch()  # must be first

import os
from erp.app import create_app
from erp.extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
