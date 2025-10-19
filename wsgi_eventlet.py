import eventlet; eventlet.monkey_patch()
from erp import create_app  # assumes app factory lives here
app = create_app()


