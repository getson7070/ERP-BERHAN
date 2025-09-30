# wsgi.py
# Entry point used by Gunicorn
from erp.app import create_app, socketio

# Gunicorn just needs the WSGI callable named `app`
app = create_app()
