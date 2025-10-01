# Patch BEFORE importing anything that might touch sockets/threads.
# This prevents Eventlet from trying to "upgrade" objects created by other libs.
try:
    import os
    os.environ.setdefault("EVENTLET_NO_GREENDNS", "yes")  # avoid greendns surprises

    import eventlet
    eventlet.monkey_patch(
        socket=True,
        select=True,
        time=True,
        thread=True,
        os=False,
        ssl=True,
        dns=False,
        subprocess=False,
    )
except Exception:
    # If eventlet isn't available at build time, don't block import; the
    # eventlet worker will still fail loudly if required.
    pass

from erp.app import create_app  # noqa: E402

# Gunicorn looks for this 'app' object.
app = create_app()
