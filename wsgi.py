# wsgi.py
"""
Export the WSGI app for gunicorn as `app` and ensure eventlet monkey_patch
happens BEFORE anything that touches sockets/threads.
"""

# --- Patch first (and keep it minimal/safe for PaaS) -------------------------
try:
    import os
    os.environ.setdefault("EVENTLET_NO_GREENDNS", "yes")  # avoid greendns surprises

    import eventlet
    eventlet.monkey_patch(
        socket=True,
        select=True,
        time=True,
        thread=True,
        os=False,       # safer in many PaaS environments
        ssl=True,
        dns=False,      # greendns disabled above
        subprocess=False,
    )
except Exception:
    # If eventlet isn't available at build time, don't block import.
    # The eventlet gunicorn worker will still run or fail loudly later.
    pass

# --- Now import the app factory (after patching) -----------------------------
from erp.app import create_app  # noqa: E402

# Gunicorn looks for this attribute when you use "wsgi:app"
app = create_app()
