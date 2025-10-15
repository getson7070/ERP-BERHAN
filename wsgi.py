import os
# Patch as early as possible for eventlet to avoid RLock warnings
try:
    import eventlet
    eventlet.monkey_patch(all=True)
except Exception:
    pass

from erp import create_app
app = create_app()

if __name__ == "__main__":
    # For local testing
    from erp.extensions import socketio
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
