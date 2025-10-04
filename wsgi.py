# wsgi.py
import eventlet
eventlet.monkey_patch()

from erp.app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    from erp.extensions import socketio  # noqa: E402
    socketio.run(app, host="0.0.0.0", port=10000)
