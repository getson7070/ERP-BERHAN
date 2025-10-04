# gunicorn.conf.py  (full replacement - repository root)
wsgi_app = "wsgi:app"
bind = "0.0.0.0:8000"
workers = 1
worker_class = "eventlet"  # must align with the chosen async stack
timeout = 120
loglevel = "info"
