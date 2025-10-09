import os
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
worker_class = "eventlet"   # matches SocketIO async_mode
workers = 1                 # scale via instances, not threads
timeout = 120
graceful_timeout = 30
