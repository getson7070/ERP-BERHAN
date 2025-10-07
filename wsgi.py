# IMPORTANT: do this before any other imports when using the eventlet worker
import eventlet
eventlet.monkey_patch()

from erp.app import create_app

# Gunicorn command expects this name: "wsgi:app"
app = create_app()
