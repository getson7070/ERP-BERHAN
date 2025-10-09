import eventlet
eventlet.monkey_patch()

from erp import create_app  # canonical factory
app = create_app()
