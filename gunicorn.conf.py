# gunicorn.conf.py
import os

# Tell Gunicorn where the app is (so you can run just: gunicorn --config gunicorn.conf.py)
wsgi_app = "wsgi:app"

# Render provides PORT; default for local is 10000
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Eventlet worker (Socket.IO / long-poll friendly)
worker_class = "eventlet"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))

# Make sure we do NOT preload the app (we want wsgi.py to run in worker import)
preload_app = False

# Reasonable timeouts for Eventlet
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Logs to stdout/stderr (so Render captures them)
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")

# Avoid any stray threads with eventlet workers
threads = 1

