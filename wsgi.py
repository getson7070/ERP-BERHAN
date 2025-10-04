import eventlet
eventlet.monkey_patch()

from erp.app import create_app  # noqa: E402
app = create_app()
