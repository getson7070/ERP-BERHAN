# gunicorn.conf.py
import os

bind = "0.0.0.0:10000"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
threads = int(os.getenv("WEB_THREADS", "8"))
worker_class = "gthread"        # <-- drop eventlet/gevent entirely
timeout = int(os.getenv("WEB_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5
errorlog = "-"
accesslog = "-"
