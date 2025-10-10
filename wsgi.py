# wsgi.py
# Ensure eventlet monkey-patch happens BEFORE any other imports (incl. Flask/Werkzeug).
import eventlet
eventlet.monkey_patch()

from erp import create_app  # after patch

app = create_app()
