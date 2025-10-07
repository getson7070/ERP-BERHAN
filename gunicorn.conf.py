# gunicorn.conf.py
bind = "0.0.0.0:10000"
workers = 1
worker_class = "eventlet"
timeout = 120
loglevel = "info"
preload_app = True  # loads app once in master, then forks (helps with patching)
