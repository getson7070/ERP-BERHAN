
import eventlet
eventlet.monkey_patch()

from erp import create_app  # do not move upward
app = create_app()

# Optional: expose socketio runner for local dev
if __name__ == "__main__":
    from erp.extensions import socketio
    socketio.run(app, host="0.0.0.0", port=10000)
