"""
WSGI entrypoint for Render. Uses eventlet (required by Flask-SocketIO).
Exports `app` for gunicorn -c gunicorn.conf.py wsgi:app
"""
import os

# IMPORTANT: monkey-patch BEFORE importing anything that does I/O
import eventlet
eventlet.monkey_patch()

from erp.app import create_app, socketio  # import your factory + socketio instance

# Create the Flask app
app = create_app()

# Optional healthcheck endpoint for Render
@app.route("/status")
def _status():
    return {"status": "ok"}, 200

# Local dev: `python wsgi.py`
if __name__ == "__main__":
    # Socket.IO dev server (not used in Render – Gunicorn runs it)
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        allow_unsafe_werkzeug=True,  # only for local dev
    )
