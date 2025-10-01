# IMPORTANT: green the stdlib before importing anything else that touches sockets/threads
try:
    import eventlet

    # Patch all: sockets, threading, time, etc. Must happen first.
    eventlet.monkey_patch(all=True)
except Exception:
    # If eventlet is not available at build time, don't block import; gunicorn's worker will still fail loudly.
    pass

from erp.app import create_app

# Gunicorn will look for this
app = create_app()
