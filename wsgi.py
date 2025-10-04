# --- critical: eventlet must patch BEFORE any other import ---
import eventlet
eventlet.monkey_patch()

from erp.app import create_app

# Gunicorn will import this
app = create_app()
