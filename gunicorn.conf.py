# gunicorn.conf.py
# ------------------------------------------------------------
# Render sets PORT; default to 10000 for local.
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# With eventlet, use a single worker and threads=1.
# Scale by processes only when needed.
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
worker_class = "eventlet"
threads = 1

# Eventlet + preload_app is a common source of greenlet errors.
preload_app = False

# Reasonable defaults for a small Render instance.
timeout = int(os.environ.get("WEB_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 2

# Logging to stdout/err so Render captures it.
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "debug")

# Limit requests to mitigate slow leaks on free dynos.
max_requests = int(os.environ.get("MAX_REQUESTS", "200"))
max_requests_jitter = int(os.environ.get("MAX_REQUESTS_JITTER", "50"))

# Respect HTTPS from Render’s proxy
forwarded_allow_ips = ["*"]
secure_scheme_headers = {
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
    "X-FORWARDED-PROTOCOL": "ssl",
}
