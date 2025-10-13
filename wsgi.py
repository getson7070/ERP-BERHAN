# wsgi.py
import os

# Patch BEFORE importing anything else that may use stdlib sockets/locks
import eventlet
eventlet.monkey_patch()

from erp import create_app  # noqa: E402

# Gunicorn points to this
app = create_app()

if __name__ == "__main__":
    # For local debugging only
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
