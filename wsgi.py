# wsgi.py
import os
import eventlet
eventlet.monkey_patch()

from erp.app import create_app, socketio

app = create_app()

@app.route("/status")
def _status():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")), allow_unsafe_werkzeug=True)
