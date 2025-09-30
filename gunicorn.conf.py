# gunicorn.conf.py
import multiprocessing
import os

# Render provides $PORT
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Use eventlet for Flask-SocketIO
worker_class = "eventlet"
workers = 1               # for Socket.IO without message_queue, keep to 1
threads = 1
worker_connections = 1000

# Reasonable timeouts for long-poll/websocket
timeout = 120
graceful_timeout = 30
keepalive = 2

# DO NOT preload with eventlet + socketio
preload_app = False

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Security headers already handled by your proxy; leave defaults here
forwarded_allow_ips = ["*"]
