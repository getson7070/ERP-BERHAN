# gunicorn.conf.py
workers = 1
threads = 1              # eventlet doesn't need threads
worker_class = "eventlet"
preload_app = False      # your log showed True; turn it off
timeout = 120
max_requests = 200
max_requests_jitter = 50
loglevel = "debug"
accesslog = "-"
errorlog = "-"
