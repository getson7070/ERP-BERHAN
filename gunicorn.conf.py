# gunicorn.conf.py
import multiprocessing
import os

bind = "0.0.0.0:" + os.getenv("PORT", "10000")
workers = int(os.getenv("WEB_CONCURRENCY", str(multiprocessing.cpu_count()))) or 2

# Use threads instead of eventlet/gevent for Python 3.13 compatibility.
worker_class = "gthread"
threads = int(os.getenv("GTHREADS", "4"))

# Give startup a little time while DB warms up
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))

# Keepalive helps with Render routing
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Access/error logs
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOGLEVEL", "info")
