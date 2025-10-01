# Patch BEFORE importing anything that might touch sockets/threads
try:
    import os
    # Avoid greendns surprises in PaaS
    os.environ.setdefault("EVENTLET_NO_GREENDNS", "yes")

    import eventlet
    # Patch only what we need; leave threading alone to avoid LocalProxy traversal issues
    eventlet.monkey_patch(
        socket=True,
        select=True,
        time=True,
        thread=False,     # <— key change: do NOT green threading to avoid JWT proxies issues
        os=False,
        ssl=True,
        dns=False,
        subprocess=False,
    )
except Exception:
    # Don't block startup—Gunicorn's eventlet worker will still run
    pass

from erp.app import create_app  # noqa: E402 (import after patching)

# Gunicorn looks for this
app = create_app()
