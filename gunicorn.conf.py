import multiprocessing
bind = "0.0.0.0:10000"
workers = max(2, multiprocessing.cpu_count() * 2 + 1)
threads = 2
worker_class = "eventlet"
timeout = 60
graceful_timeout = 30
preload_app = True
loglevel = "info"
