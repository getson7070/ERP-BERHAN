# wsgi.py  (monkey-patch FIRST and only here)
import eventlet
eventlet.monkey_patch()

from erp.app import create_app
from erp.extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
