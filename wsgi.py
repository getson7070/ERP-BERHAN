# Patch BEFORE importing anything that might touch sockets/threads
try:
    # A couple of env toggles that make patching less invasive in containerized envs
    import os
    os.environ.setdefault("EVENTLET_NO_GREENDNS", "yes")  # avoid greendns surprises

    import eventlet
    # Patch common subsystems; doing it here keeps it earliest in import order
    eventlet.monkey_patch(
        socket=True,
        select=True,
        time=True,
        thread=True,
        os=False,        # safer in many PaaS environments
        ssl=True,
        dns=False,       # greendns disabled above
        subprocess=False
        # (aggressive defaults to True; leaving it as default is fine now that
        # flask_jwt_extended won't be imported yet—see extensions.py)
    )
except Exception:
    # Don't block startup—Gunicorn's eventlet worker still runs; we just lose some greening
    pass

from erp.app import create_app  # noqa: E402  (import after patching)

# Gunicorn looks for "app"
app = create_app()
