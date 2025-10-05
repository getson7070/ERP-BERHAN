# wsgi.py
import eventlet
eventlet.monkey_patch()  # must be before any other imports

from erp.app import create_app

app = create_app()  # Gunicorn entry: "wsgi:app"
