# wsgi.py
import eventlet
eventlet.monkey_patch()  # must be first

from erp import create_app
app = create_app()
