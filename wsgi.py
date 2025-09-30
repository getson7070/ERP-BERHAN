import eventlet
eventlet.monkey_patch(all=True)

from erp.app import create_app, socketio  # noqa: E402

app = create_app()

if __name__ == "__main__":
    import os
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
