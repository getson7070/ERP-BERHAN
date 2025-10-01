# gunicorn.conf.py
import multiprocessing
import os

wsgi_app = "wsgi:app"

# Eventlet for Flask-SocketIO
worker_class = "eventlet"
workers = 1  # eventlet is async; one worker is typical with SocketIO

# Bind to Render's assigned port
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Timeouts
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))

# Logging
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")

# Avoid tmpfs issues
worker_tmp_dir = "/dev/shm"
