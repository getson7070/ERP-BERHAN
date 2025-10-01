# Eventlet worker for long-lived Socket.IO connections
worker_class = "eventlet"
workers = 1
worker_connections = 1000

# Network
bind = "0.0.0.0:10000"
timeout = 120
keepalive = 5
graceful_timeout = 30

# App loading
preload_app = False  # keep False when using eventlet unless you control import order

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
