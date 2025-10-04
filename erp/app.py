# erp/app.py
import os
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from limits.util import parse_many

def _normalize_limits(s: str) -> str:
    """
    Accepts strings like '300 per minute; 30 per second' or '300/minute;30/second'
    and normalizes to the latter so limits.parse_many() always works.
    """
    s = (s or "300/minute;30/second").strip()
    s = s.replace(" per ", "/").replace(" ", "")
    # Normalize shorthands that might slip in
    s = s.replace("/min", "/minute").replace("/sec", "/second").replace("/hr", "/hour")
    return s

def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Core config
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        os.environ.get("SQLALCHEMY_DATABASE_URI")
        or os.environ.get("DATABASE_URL")
    )

    # CORS
    origins = os.environ.get("CORS_ORIGINS", "*")
    origins_list = [o.strip() for o in origins.split(",")] if origins else ["*"]
    CORS(app, resources={r"/*": {"origins": origins_list}})

    # Rate limiting
    storage_uri = (
        os.environ.get("FLASK_LIMITER_STORAGE_URI")
        or os.environ.get("RATELIMIT_STORAGE_URI")
        or "memory://"
    )
    default_limits = parse_many(_normalize_limits(os.environ.get("DEFAULT_RATE_LIMITS")))
    Limiter(get_remote_address, app=app, storage_uri=storage_uri, default_limits=default_limits)

    # Jinja helpers so templates using _() won't crash
    @app.context_processor
    def inject_helpers():
        return {"_": (lambda s: s)}

    # Blueprints
    from .web import web_bp
    app.register_blueprint(web_bp)

    return app
