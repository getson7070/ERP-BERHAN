# gunicorn.conf.py
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
worker_class = "eventlet"
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("THREADS", "1"))
timeout = int(os.environ.get("TIMEOUT", "120"))
graceful_timeout = int(os.environ.get("GRACEFUL_TIMEOUT", "30"))
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
