# Minimal WSGI entrypoint using the canonical factory
from erp.app import create_app
app = create_app()

class HealthAliasMiddleware:
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        if environ.get("REQUEST_METHOD") == "GET" and environ.get("PATH_INFO") == "/health":
            start_response("200 OK", [("Content-Type","text/plain")])
            return [b"ok"]
        return self.app(environ, start_response)

app = HealthAliasMiddleware(app)
