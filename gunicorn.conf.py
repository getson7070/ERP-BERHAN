# Gunicorn config for Flask-SocketIO (eventlet) on Render
import os

bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# IMPORTANT: eventlet worker for WebSocket support
worker_class = "eventlet"

# With eventlet one worker is usually fine; scale out with Render autoscaling if needed
workers = int(os.getenv("WEB_CONCURRENCY", "1"))

# Do NOT preload; we must monkey_patch before imports (done in wsgi.py)
preload_app = False

# Keep defaults sensible
threads = 1
worker_connections = 1000
timeout = int(os.getenv("WEB_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 2

# Trust Render’s proxy headers
forwarded_allow_ips = ['*']
secure_scheme_headers = {
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-SSL": "on",
}

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "debug")
