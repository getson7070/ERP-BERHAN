# wsgi.py
import os
import eventlet
eventlet.monkey_patch()  # must happen before anything else

from erp.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
