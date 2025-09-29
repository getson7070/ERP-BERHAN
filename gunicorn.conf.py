# gunicorn.conf.py  — low-memory + verbose logs
workers = 1
threads = 2
worker_class = "sync"
preload_app = False
timeout = 120
max_requests = 200
max_requests_jitter = 50
loglevel = "debug"
accesslog = "-"
errorlog = "-"
