# wsgi.py  (full replacement - repository root)
from erp.app import create_app
from erp.extensions import socketio

app = create_app()

if __name__ == "__main__":
    # For local runs only. In Render, Gunicorn will import "wsgi:app".
    socketio.run(app, host="0.0.0.0", port=8000)
