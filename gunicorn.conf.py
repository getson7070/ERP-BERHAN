import multiprocessing
import os

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "8"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "eventlet")
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
preload_app = True
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
