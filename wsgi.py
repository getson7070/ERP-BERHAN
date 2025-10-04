# wsgi.py — ensure eventlet patches happen before any other import
import eventlet
eventlet.monkey_patch()

from erp.app import create_app
from erp.extensions import socketio

app = create_app(

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
