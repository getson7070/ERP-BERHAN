# wsgi.py
import os

# Patch BEFORE any other imports so eventlet works with gunicorn and Flask-SocketIO
try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    # If eventlet isn't present, we’ll run in threading mode.
    pass

from erp import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # Development runner; on Render you use gunicorn.
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
