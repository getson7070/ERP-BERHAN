# wsgi.py
import eventlet
eventlet.monkey_patch()  # MUST happen before any other imports when using eventlet workers

from erp.app import create_app

# Gunicorn runs "wsgi:app" so we must expose a module-level "app"
app = create_app()

if __name__ == "__main__":
    app.run()
