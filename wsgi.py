# Always monkey-patch FIRST, before ANY other imports.
import eventlet
eventlet.monkey_patch()  # <- fixes the "monkey_patching" & app/request context explosions

import os
# wsgi.py
from app import create_app, socketio  # assuming your app factory is in app.py

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)

# Your application package is "erp" (as seen in log records: name="erp")
from erp import create_app, socketio  # create_app must build the Flask app; socketio is your SocketIO() instance

# Build app AFTER monkey_patch so imports are safe
app = create_app()

# When running under gunicorn -k eventlet, exposing the Flask app object is enough.
# Gunicorn handles the eventlet worker. For local dev: `python wsgi.py`
if __name__ == "__main__":
    # Make local runs behave the same (eventlet)
    port = int(os.getenv("PORT", "10000"))
    # cert/keys can be added here if you terminate TLS locally
    socketio.run(app, host="0.0.0.0", port=port)
