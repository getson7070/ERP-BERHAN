# gunicorn.conf.py
import os

bind = "0.0.0.0:" + os.getenv("PORT", "10000")
worker_class = "eventlet"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
worker_connections = 1000
timeout = 60
graceful_timeout = 60
keepalive = 5
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
