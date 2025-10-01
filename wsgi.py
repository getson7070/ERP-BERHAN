# wsgi.py
"""
Entry point for Gunicorn. We must monkey-patch Eventlet
*before* importing anything that might touch sockets/threads.
"""

# --- Eventlet greening early ---
try:
    import os

    # Keep DNS/os patching conservative in PaaS containers.
    os.environ.setdefault("EVENTLET_NO_GREENDNS", "yes")

    import eventlet

    eventlet.monkey_patch(
        socket=True,
        select=True,
        time=True,
        thread=True,
        os=False,        # safer in containers
        ssl=True,
        dns=False,       # greendns disabled above
        subprocess=False
    )
except Exception:
    # If Eventlet isn't importable here, don't prevent process startup.
    # Gunicorn's eventlet worker will still run; you'll just lose some greening.
    pass

# --- Now import the app factory (safe after greening) ---
from erp.app import create_app  # noqa: E402

# Gunicorn looks for "app"
app = create_app()
