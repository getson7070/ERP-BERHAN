# wsgi.py
import os

# Eventlet must patch BEFORE any other imports (especially anything that
# might import flask_jwt_extended and create LocalProxy objects).
os.environ.setdefault("EVENTLET_NO_GREENDNS", "yes")

import eventlet  # noqa: E402
# Avoid patching threading to prevent Eventlet from traversing LocalProxy
# instances (which triggers app/request context lookups). Socket/time/select
# are what we need for Gunicorn eventlet workers + Socket.IO.
eventlet.monkey_patch(thread=False)

# Now it is safe to import your app
from erp.app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    # Local dev convenience
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
