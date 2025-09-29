# wsgi.py
# ------------------------------------------------------------
# MUST be the first imports to avoid greenlet/thread errors.
import eventlet
eventlet.monkey_patch()

import os

# Import your Flask app in a way that works whether the package
# is named "app" or "erp". Only ONE of these will succeed.
flask_app = None
socketio = None

try:
    # If your project exposes factory & socketio here
    from app import create_app, socketio as _socketio  # type: ignore
    flask_app = create_app()
    socketio = _socketio
except Exception:
    pass

if flask_app is None:
    try:
        # Alternate common layout: package is "erp"
        from erp import create_app, socketio as _socketio  # type: ignore
        flask_app = create_app()
        socketio = _socketio
    except Exception as e:
        # Last fallback: the app object may already be constructed
        try:
            from app import app as flask_app  # type: ignore
        except Exception:
            from erp import app as flask_app  # type: ignore
        socketio = None  # will still work for plain HTTP

# Gunicorn looks for a variable called "app".
app = flask_app

# Local development (Render won’t execute this block)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    host = "0.0.0.0"
    if socketio:
        # Ensure eventlet async mode
        from flask_socketio import SocketIO  # noqa
        socketio.async_mode = "eventlet"  # enforce
        socketio.run(app, host=host, port=port)
    else:
        # No socketio object exposed -> run plain Flask
        from werkzeug.serving import run_simple
        run_simple(host, port, app)
