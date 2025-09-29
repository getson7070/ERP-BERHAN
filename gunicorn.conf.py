# gunicorn.conf.py
import os

# Render assigns a port via the PORT env var. Never hardcode.
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Flask-SocketIO + Gunicorn should use an async worker.
# eventlet is already in your requirements and avoids the greenlet/thread switch error.
worker_class = "eventlet"
workers = 1          # eventlet: 1 worker handles many sockets cooperatively
threads = 1
preload_app = True

# Keep logs helpful but not too noisy.
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Make sure this is a STRING, not a list, or Gunicorn will abort at startup.
# Your logs showed: Invalid value for forwarded_allow_ips: ['*']
forwarded_allow_ips = "*"

# A couple of sensible limits for basic stability.
timeout = 120
graceful_timeout = 30
keepalive = 2

# If you previously set any sync-specific options (e.g., worker_connections for gevent/eventlet
# is fine; gunicorn defaults are OK) you can add them here; not strictly needed.
