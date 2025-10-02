# wsgi.py
# Do NOT call eventlet.monkey_patch() here; Gunicorn eventlet worker patches early.
from erp.app import create_app

app = create_app()
