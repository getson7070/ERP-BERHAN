import eventlet
eventlet.monkey_patch()

from erp import create_app
app = create_app()

# optional: expose socketio if you're using it, e.g. in Render shell
try:
    from erp.extensions import socketio
except Exception:
    socketio = None

if __name__ == "__main__":
    if socketio:
        socketio.run(app, host="0.0.0.0", port=5000)
    else:
        app.run(host="0.0.0.0", port=5000)
