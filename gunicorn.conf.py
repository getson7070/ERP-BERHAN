# Gunicorn config for Render + Flask-SocketIO (eventlet)
import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))  # eventlet does not need many
worker_class = "eventlet"
threads = 1               # don't combine threads with eventlet
worker_connections = 1000 # sockets per worker
timeout = 120
graceful_timeout = 30
keepalive = 2
preload_app = False       # eventlet + socketio prefers not to preload
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Security headers forwarded by Render
secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
}
forwarded_allow_ips = ["*"]
