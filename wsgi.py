# wsgi.py
import eventlet
eventlet.monkey_patch()  # MUST be before any other imports

from erp.app import create_app

app = create_app()
