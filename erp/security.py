"""ERP security setup: CSRF + context processor for csrf_token()."""
import os
from flask import current_app
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

csrf = CSRFProtect()

def init_app(app):
    # SECRET_KEY must be stable in production
    secret = app.config.get("SECRET_KEY") or os.getenv("SECRET_KEY")
    if not secret and app.config.get("ENV") == "production":
        raise RuntimeError("SECRET_KEY is required in production. Set the SECRET_KEY environment variable.")
    if not secret:
        # Dev fallback to avoid 500s on flash/session locally
        secret = "dev-" + os.urandom(32).hex()
    app.config["SECRET_KEY"] = secret

    csrf.init_app(app)

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)
