# wsgi.py
import os

# MUST patch before importing anything else that does I/O
import eventlet
eventlet.monkey_patch()

from erp import create_app, socketio  # noqa: E402

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    # Use SocketIO runner (eventlet)
    socketio.run(app, host="0.0.0.0", port=port)
