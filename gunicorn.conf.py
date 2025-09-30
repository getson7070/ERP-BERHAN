# gunicorn.conf.py
import os

bind = "0.0.0.0:10000"  # Render discovers the port automatically
workers = 1             # increase after DB/Redis are ready
threads = 2
worker_class = "eventlet"
timeout = 120
graceful_timeout = 30
loglevel = "debug"
preload_app = True

# Health: restart workers periodically to avoid leaks
max_requests = 200
max_requests_jitter = 50

# Environment consistency
raw_env = [
    f"APP_ENV={os.environ.get('APP_ENV', 'development')}",
]
