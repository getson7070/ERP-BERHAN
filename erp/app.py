# erp/app.py
from __future__ import annotations

import os
import re
from typing import Optional

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Global extensions (kept simple) ---
db = SQLAlchemy()
migrate = Migrate()
limiter: Optional[Limiter] = None


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None else default


def _db_uri() -> str:
    # Prefer SQLALCHEMY_DATABASE_URI; fall back to DATABASE_URL
    uri = _env("SQLALCHEMY_DATABASE_URI") or _env("DATABASE_URL")
    if not uri:
        raise RuntimeError(
            "Either 'SQLALCHEMY_DATABASE_URI' or 'DATABASE_URL' must be set."
        )
    return uri


def _fix_limits_string(s: str) -> str:
    """
    Accepts many human inputs:
      - '300/min', '300 per min', '300 per minute'
      - '30/sec', '30 per sec', '30 per second'
    and normalizes them to 'per minute' and 'per second' so limits.parse_many() won't 500.
    """
    if not s:
        return ""
    parts = []
    for raw in s.split(";"):
        t = raw.strip().lower()
        if not t:
            continue
        # normalize shorthands and slashed forms
        t = re.sub(r"/\s*(min(ute)?|m)\b", " per minute", t)
        t = re.sub(r"\bper\s+min(ute)?\b", " per minute", t)
        t = re.sub(r"/\s*(sec(ond)?|s)\b", " per second", t)
        t = re.sub(r"\bper\s+sec(ond)?\b", " per second", t)
        parts.append(t)
    return "; ".join(parts)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Secret key
    app.config["SECRET_KEY"] = _env("FLASK_SECRET_KEY", "dev-secret-not-for-prod")

    # DB config
    app.config["SQLALCHEMY_DATABASE_URI"] = _db_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Caching (initialized only if you later wire it in erp/cache.py)
    app.config["CACHE_TYPE"] = _env("CACHE_TYPE", "SimpleCache")
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(_env("CACHE_DEFAULT_TIMEOUT", "300"))

    # CORS
    origins = _env("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": origins}}, supports_credentials=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=_env("FLASK_LIMITER_STORAGE_URI", _env("RATELIMIT_STORAGE_URI", "memory://")),
        default_limits=[],
        headers_enabled=True,
    )
    limiter.init_app(app)

    # Normalize default limits coming from env (avoids 'no granularity matched for min')
    default_limits = _env("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
    limiter.default_limits = _fix_limits_string(default_limits)

    # Provide a safe '_' to templates so {{ _('Login') }} never explodes if Babel isn't configured
    @app.context_processor
    def _inject_jinja_helpers():
        def _(s: str) -> str:
            return s
        return {"_": _}

    # --- Blueprints ---
    from erp.web import web_bp  # lightweight routes & health
    app.register_blueprint(web_bp)

    # Real auth blueprint that builds/wires a LoginForm and renders templates with 'form'
    try:
        from erp.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix="/auth")
    except Exception as e:
        # If auth blueprint has optional imports, app still boots; /auth/* will 404.
        app.logger.warning(f"[blueprints] auth blueprint not registered: {e}")

    # Exempt health from limiting (by endpoint name)
    try:
        app.view_functions  # ensure created
        limiter.exempt(app.view_functions.get("web.health"))
    except Exception:
        pass

    return app
