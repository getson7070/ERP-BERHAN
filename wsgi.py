# patch Eventlet BEFORE anything else is imported
import eventlet
eventlet.monkey_patch()

import os
from erp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
