# gunicorn.conf.py
import os
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
worker_class = "eventlet"
threads = 1
worker_connections = 1000
timeout = 120
graceful_timeout = 30
keepalive = 2
preload_app = False
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
}
forwarded_allow_ips = "*"
