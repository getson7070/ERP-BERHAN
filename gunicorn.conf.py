# gunicorn.conf.py
bind = "0.0.0.0:18000"
workers = 2
threads = 4
timeout = 60
worker_class = "gthread"
# accesslog = "-"       # optional: stdout
# errorlog  = "-"       # optional: stdout
