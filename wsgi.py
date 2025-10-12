# >>> add these two lines at the very top <<<
import eventlet
eventlet.monkey_patch()

import os
from erp import create_app

app = create_app()

if __name__ == "__main__":
    # Never hardcode port on Render; use $PORT
    port = int(os.environ.get("PORT", 8000))
    # Use a simple dev server only when running locally
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", port, app, use_reloader=False)
