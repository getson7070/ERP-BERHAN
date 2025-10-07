import eventlet
eventlet.monkey_patch()  # MUST run before any other imports that use networking/threads

from erp.app import create_app
from erp.extensions import socketio

app = create_app()

# For local dev: `python wsgi.py`
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "10000"))
    socketio.run(app, host="0.0.0.0", port=port)
