# wsgi.py
# IMPORTANT: monkey-patch BEFORE importing anything that might use threading/ssl/etc.
import eventlet
eventlet.monkey_patch()

from erp.app import create_app

# Gunicorn loads this as "wsgi:app"
app = create_app()

# Optional: make local run easy
if __name__ == "__main__":
    # Use eventlet WSGI server for local tests
    from eventlet import wsgi as eventlet_wsgi
    eventlet_wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)
