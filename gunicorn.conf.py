import os, eventlet
eventlet.monkey_patch()

bind = "0.0.0.0:10000"
worker_class = "eventlet"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
preload_app = False
