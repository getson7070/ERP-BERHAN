# erp/app.py
import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from jinja2 import ChoiceLoader, FileSystemLoader

db = SQLAlchemy()
migrate = Migrate()

# Create the limiter object first; init in create_app to avoid circulars.
limiter = Limiter(key_func=get_remote_address, default_limits=[])

def _parse_default_limits():
    """
    Accept semicolon or comma separated strings. Normalize common shorthands.
    Examples accepted:
      "300 per minute; 30 per second"   or   "300/minute, 30/second"
    """
    raw = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
    parts = [p.strip() for p in raw.replace(",", ";").split(";") if p.strip()]
    fixed = []
    for p in parts:
        p = (p
             .replace("/sec", "/second")
             .replace(" per sec", " per second")
             .replace("/min", "/minute")
             .replace(" per min", " per minute"))
        # limits understands either "X per minute" or "X/minute"
        fixed.append(p)
    return fixed

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",   # project-root/templates
        static_folder="static"
    )

    # --- Config basics ---
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
        or "sqlite:////tmp/erp.db"  # safe fallback so app boots even without DB
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)

    CORS(app, resources={r"/*": {
        "origins": [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
    }})

    # Look for templates in BOTH locations: /templates and /erp/templates
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(os.path.join(repo_root, "templates")),
        FileSystemLoader(os.path.join(repo_root, "erp", "templates")),
    ])

    # Limiter – fix the “no granularity matched for min” crash
    limiter.default_limits = _parse_default_limits()
    limiter.storage_uri = (
        os.getenv("FLASK_LIMITER_STORAGE_URI")
        or os.getenv("RATELIMIT_STORAGE_URI")
        or "memory://"
    )
    limiter.init_app(app)

    # Make {{_()}} available so templates with i18n calls don’t blow up
    @app.context_processor
    def inject_helpers():
        return {"_": (lambda s, **kwargs: s)}

    # Register the thin web blueprint (doesn't import heavy modules)
    from .web import web_bp
    app.register_blueprint(web_bp)

    return app
