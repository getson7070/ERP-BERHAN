import eventlet
eventlet.monkey_patch()

from erp import create_app

app = create_app()


