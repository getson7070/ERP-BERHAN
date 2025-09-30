import os

# Bind to Render’s assigned port
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Use threads (no eventlet/gevent on Python 3.13)
worker_class = "gthread"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = int(os.environ.get("WEB_THREADS", "4"))
timeout = int(os.environ.get("WEB_TIMEOUT", "120"))
keepalive = 30
graceful_timeout = 30
worker_tmp_dir = "/dev/shm"
loglevel = os.environ.get("LOG_LEVEL", "info")
