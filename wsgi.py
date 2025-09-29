# wsgi.py
# ─────────────────────────────────────────────────────────────────────────────
# MUST be the very first imports so all stdlib is greenlet-patched
import os

# Eventlet is required by Flask-SocketIO when using the 'eventlet' async mode.
# The monkey patch MUST happen before importing ANY other blocking libs
# (Flask, requests, Redis, etc.).
import eventlet
eventlet.monkey_patch(all=True, thread=True, socket=True, select=True, time=True)

from dotenv import load_dotenv
load_dotenv()  # lets Render env and .env both work locally

# Import the application factory and the global Socket.IO object.
# NOTE: keep these imports AFTER monkey_patch.
try:
    # if your package is named 'erp' (your logger shows name 'erp')
    from erp import create_app, socketio  # type: ignore
except ImportError:
    # fallback if app is at top-level as app.py
    from app import create_app, socketio  # type: ignore

# Create the Flask app via factory
# FLASK_ENV can be 'production' | 'development' etc.; default production
flask_env = os.getenv("FLASK_ENV", "production")
app = create_app(flask_env)

# Gunicorn entrypoint expects an `app` object in this module
# Keep this file lean – all blueprints/config load inside create_app()

# Optional: a simple health-check root (keeps "/" from erroring when no route)
# If you already have a "/" route, you can drop this.
@app.route("/", methods=["GET", "HEAD"])
def _health_root():
    return "OK", 200

# Local dev runner (not used on Render – gunicorn runs this module)
if __name__ == "__main__":
    # Bind to PORT for local runs; default 5000
    port = int(os.getenv("PORT", "5000"))
    # IMPORTANT: use eventlet web server so Socket.IO works in dev too
    socketio.run(app, host="0.0.0.0", port=port)
