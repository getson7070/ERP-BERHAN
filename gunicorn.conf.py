# gunicorn.conf.py
import os

# Render sets PORT; default to 10000 for local/run.
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Eventlet worker for Socket.IO / long polling
worker_class = "eventlet"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))

# Timeouts appropriate for Eventlet
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Logging to stdout/stderr
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
