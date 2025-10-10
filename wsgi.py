# wsgi.py
try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    pass

from erp import create_app
app = create_app()
