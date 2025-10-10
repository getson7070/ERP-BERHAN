import eventlet
eventlet.monkey_patch()  # must be before any other imports

from erp import create_app
app = create_app()
