# wsgi.py
import os
import eventlet

# IMPORTANT: monkey patch BEFORE importing anything else that uses networking
eventlet.monkey_patch()

from app import create_app, socketio  # <-- no circular import anymore

# Create the Flask app via the factory
app = create_app()

# When running directly (e.g., local dev: `python wsgi.py`), start Socket.IO server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # With eventlet this will serve both HTTP and WebSocket on one port
    socketio.run(app, host="0.0.0.0", port=port)
