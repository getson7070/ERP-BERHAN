# eventlet must patch before any stdlib/network import when using eventlet workers
import eventlet
eventlet.monkey_patch()

from erp import create_app

# Gunicorn entrypoint: wsgi:app
app = create_app()
