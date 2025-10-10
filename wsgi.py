# wsgi.py
import eventlet
eventlet.monkey_patch()

from erp import create_app
app = create_app()

if __name__ == "__main__":
    # For local debugging only
    from erp.extensions import socketio
    socketio.run(app, host="0.0.0.0", port=5000)
