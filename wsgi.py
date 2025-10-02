# wsgi.py
"""
WSGI entrypoint for Render & Gunicorn.
Eventlet must be monkey-patched BEFORE any other imports.
"""
import os
import eventlet

eventlet.monkey_patch()

from erp.app import create_app  # noqa: E402  (import after monkey_patch)

app = create_app()

if __name__ == "__main__":
    # Local dev convenience (not used by Render)
    from eventlet import wsgi
    port = int(os.getenv("PORT", "5000"))
    wsgi.server(eventlet.listen(("0.0.0.0", port)), app)
