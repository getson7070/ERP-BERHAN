# IMPORTANT: patch BEFORE importing anything that creates threads/sockets
import eventlet
eventlet.monkey_patch()

from erp.app import create_app
from erp.extensions import socketio

# Gunicorn will import this symbol
app = create_app()

# Local/dev runner: "python wsgi.py"
if __name__ == "__main__":
    # allow_unsafe_werkzeug=True is fine for local use
    port = int(os.getenv("PORT", "5000"))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
