# wsgi.py
# IMPORTANT: monkey_patch BEFORE importing anything else that uses sockets/threads
import eventlet
eventlet.monkey_patch()

from erp import create_app
app = create_app()

# optional: small health check for Render
@app.route("/health")
def health():
    return "ok"
