import multiprocessing

bind = "0.0.0.0:10000"
workers = 1
worker_class = "eventlet"
threads = 1
timeout = 120
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
