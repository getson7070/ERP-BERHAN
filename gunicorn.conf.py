# gunicorn.conf.py
import os

bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "8"))
workers = int(os.getenv("WEB_CONCURRENCY", "1"))

timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
