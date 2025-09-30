# Keep this simple and 3.13-safe — no eventlet.
bind = "0.0.0.0:10000"
workers = 2
worker_class = "gthread"
threads = 8
timeout = 120
graceful_timeout = 30
loglevel = "info"
# If you see CPU throttling on free tier, reduce threads to 4.
