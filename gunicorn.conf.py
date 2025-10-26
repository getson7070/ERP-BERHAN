bind = "0.0.0.0:8000"
wsgi_app = "wsgi:app"

# Eventlet, since your code references eventlet and expects greened libs
worker_class = "eventlet"
workers = 2
worker_connections = 1000

timeout = 60
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
