# wsgi.py
# IMPORTANT: eventlet must be monkey-patched BEFORE importing anything else.
import eventlet  # type: ignore
eventlet.monkey_patch()

from erp import create_app, socketio  # noqa

app = create_app()

# For local runs only; Render will run gunicorn against `wsgi:app`
if __name__ == "__main__":
    # Uses eventlet by default via SocketIO
    socketio.run(app, host="0.0.0.0", port=5000)
