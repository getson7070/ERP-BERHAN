import os
import eventlet
eventlet.monkey_patch()  # must be before any other imports when using eventlet

from erp.app import create_app
from erp.extensions import socketio  # initialized in init_extensions

app = create_app()

# Optional: run directly (dev). On Render, gunicorn runs this file.
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
