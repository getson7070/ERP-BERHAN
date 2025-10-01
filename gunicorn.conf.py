# gunicorn.conf.py
import multiprocessing, os
bind = "0.0.0.0:" + os.getenv("PORT", "10000")
workers = 1  # eventlet works with single worker
worker_class = "eventlet"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOGLEVEL", "info")
