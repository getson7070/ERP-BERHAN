# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:10000"
worker_class = "eventlet"
workers = 1
threads = 1
timeout = int(120)
graceful_timeout = int(120)
loglevel = "info"
