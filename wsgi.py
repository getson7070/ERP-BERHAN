# wsgi.py — entrypoint for Gunicorn on Render

# IMPORTANT: eventlet must be patched before importing anything else
import eventlet
eventlet.monkey_patch()

from erp import create_app

# Gunicorn looks for 'app'
app = create_app()

# Optional local run (Render won’t use this)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
