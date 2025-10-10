import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1                # Socket.IO + eventlet prefers 1 worker
worker_class = "eventlet"  # match your Socket.IO async mode
threads = 1
timeout = 120
graceful_timeout = 120
preload_app = False        # with eventlet, avoid preloading unless you know it's safe
