# gunicorn.conf.py
import multiprocessing, os

bind = "0.0.0.0:" + os.getenv("PORT", "10000")
workers = int(os.getenv("WEB_CONCURRENCY", str(max(2, multiprocessing.cpu_count()))))
worker_class = "gthread"
threads = int(os.getenv("GTHREADS", "4"))

timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOGLEVEL", "info")