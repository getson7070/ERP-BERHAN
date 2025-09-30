# gunicorn.conf.py
import os

# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:10000"
workers = 1  # Render free tier small, keep 1 worker
worker_class = "eventlet"
threads = 2
timeout = 120
preload_app = True


# Health: restart workers periodically to avoid leaks
max_requests = 200
max_requests_jitter = 50

# Environment consistency
raw_env = [
    f"APP_ENV={os.environ.get('APP_ENV', 'development')}",
]
