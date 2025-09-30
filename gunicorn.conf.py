# gunicorn.conf.py
import multiprocessing
import os

bind = "0.0.0.0:" + os.getenv("PORT", "10000")

# IMPORTANT: use gevent workers (not eventlet)
worker_class = "gevent"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
worker_connections = 1000
timeout = 60
graceful_timeout = 60
keepalive = 5
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
