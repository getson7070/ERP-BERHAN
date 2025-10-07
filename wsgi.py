# wsgi.py
import eventlet
eventlet.monkey_patch()  # must be first

from erp.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
