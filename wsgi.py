import json
from erp import create_app

_flask = create_app()

def _health_wsgi(environ, start_response):
    path = environ.get("PATH_INFO", "")
    if path in ("/healthz", "/health/ready", "/health/live"):
        body = b"{\"ok\":true}"
        start_response("200 OK", [
            ("Content-Type","application/json"),
            ("Content-Length", str(len(body)))
        ])
        return [body]
    return _flask(environ, start_response)

# Gunicorn entrypoint
app = _health_wsgi