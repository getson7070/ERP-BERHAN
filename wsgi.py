import eventlet
eventlet.monkey_patch()
# wsgi.py
# Do eventlet monkey patching BEFORE any other imports to avoid green/thread issues.

from erp import create_app

app = create_app()

# Optional local run:
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
