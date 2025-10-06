# wsgi.py
import os

# IMPORTANT: monkey_patch BEFORE importing anything that uses sockets/locks/threads.
if os.getenv("USE_EVENTLET", "1") == "1":
    import eventlet
    eventlet.monkey_patch()

from erp.app import create_app
from erp.extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # SocketIO dev server; Gunicorn will run this module in Render.
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True, debug=True)
