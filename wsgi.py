# wsgi.py
from erp.app import create_app, socketio

app = create_app()

# Gunicorn will import "wsgi:app". We do NOT call socketio.run() here.
# Worker type is configured in gunicorn.conf.py.
