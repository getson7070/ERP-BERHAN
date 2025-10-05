# gunicorn.conf.py
import os
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
worker_class = "eventlet"
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
