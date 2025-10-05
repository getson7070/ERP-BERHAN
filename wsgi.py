import os
try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    pass

from erp.app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
