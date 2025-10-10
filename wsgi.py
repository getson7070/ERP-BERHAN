# wsgi.py
import eventlet
eventlet.monkey_patch()  # MUST be first import

from erp import create_app

# Gunicorn entrypoint
app = create_app()
