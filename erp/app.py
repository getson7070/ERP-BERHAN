# erp/app.py
import os
import pkgutil
import importlib
from typing import Iterable, Optional

from flask import Flask, redirect, url_for, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Blueprint

from .extensions import init_extensions, db

# ---- Helpers ---------------------------------------------------------------

def _coerce_sqlalchemy_uri() -> Optional[str]:
    """
    Prefer explicit SQLALCHEMY_DATABASE_URI. Otherwise adapt DATABASE_URL
    for SQLAlchemy. Also normalize 'postgres://' -> 'postgresql://' and
    append '?sslmode=require' if connecting to a managed host and none provided.
    """
    uri = os.getenv("SQLALCHEMY_DATABASE_URI")
    if not uri:
        uri = os.getenv("DATABASE_URL")

    if not uri:
        return None

    # Normalize scheme for SQLAlchemy
    if uri.startswith("postgres://"):
        uri = "postgresql://" + uri[len("postgres://"):]

    # Ensure driver is psycopg2 if not specified
    if uri.startswith("postgresql://") and "+psycopg2" not in uri:
        uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Add sslmode=require if connecting to Render/managed PG without explicit sslmode
    if "render.com" in uri and "sslmode=" not in uri:
        sep = "&" if "?" in uri else "?"
        uri = f"{uri}{sep}sslmode=require"

    return uri


def _try_url_for(endpoint: str, default: str):
    try:
        return url_for(endpoint)
    except Exception:
        return default


def _iter_submodules(package_name: str) -> Iterable[str]:
    """
    Yields full module names for immediate submodules in `package_name`.
    Only .py files (no nested packages) unless a directory is a package with __init__.
    """
    try:
        package = importlib.import_module(package_name)
    except Exception:
        return []
    package_path = getattr(package, "__path__", None)
    if not package_path:
        return []

    for modinfo in pkgutil.iter_modules(package_path):
        yield f"{package_name}.{modinfo.name}"


def _register_blueprint_from_module(app: Flask, module_name: str, registered_names: set):
    """
    Import `module_name` and register its module-level Blueprint `bp` if present,
    guarding against duplicates by blueprint NAME (Blueprint.name).
    """
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return

    bp = getattr(mod, "bp", None)
    if not isinstance(bp, Blueprint):
        return

    # Ensure unique blueprint name (what Flask uses internally)
    if bp.name in registered_names:
        # Already registered; skip
        return

    # Optional per-module URL prefix: __URL_PREFIX__ or 'url_prefix'
    url_prefix = getattr(mod, "__URL_PREFIX__", None) or getattr(mod, "url_prefix", None)

    # If module is under erp.api.*, prefix with /api by default
    if url_prefix is None and module_name.startswith("erp.api."):
        url_prefix = "/api"

    app.register_blueprint(bp, url_prefix=url_prefix)
    registered_names.add(bp.name)


def _auto_register_blueprints(app: Flask):
    """
    Auto-discover and register blueprints in:
      - erp.routes.*   (site/UI)
      - erp.api.*      (REST/JSON)
    Avoids duplicate registration if the same blueprint is imported twice.
    """
    registered_names: set = set()

    for root_pkg in ("erp.routes", "erp.api"):
        for modname in _iter_submodules(root_pkg):
            _register_blueprint_from_module(app, modname, registered_names)


# ---- App Factory -----------------------------------------------------------

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # Make Flask aware it's behind Render's proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)  # type: ignore

    # --- Config --------------------------------------------------------------
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    # SQLAlchemy / Postgres
    uri = _coerce_sqlalchemy_uri()
    if not uri:
        raise RuntimeError("Either 'SQLALCHEMY_DATABASE_URI' or 'DATABASE_URL' must be set.")
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # CORS
    app.config.setdefault("CORS_ORIGINS", os.getenv("CORS_ORIGINS", "*"))

    # Caching (default to simple to avoid warnings)
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "simple"))

    # Limiter / Redis
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("RATELIMIT_STORAGE_URI", ""))

    # Socket.IO message queue (optional)
    app.config.setdefault("SOCKETIO_MESSAGE_QUEUE", os.getenv("SOCKETIO_MESSAGE_QUEUE", ""))

    # Babel default locale/timezone
    app.config.setdefault("BABEL_DEFAULT_LOCALE", os.getenv("BABEL_DEFAULT_LOCALE", "en"))
    app.config.setdefault("BABEL_DEFAULT_TIMEZONE", os.getenv("BABEL_DEFAULT_TIMEZONE", "UTC"))

    # --- Init extensions -----------------------------------------------------
    init_extensions(app)

    # --- Blueprints ----------------------------------------------------------
    _auto_register_blueprints(app)

    # --- Health --------------------------------------------------------------
    @app.get("/health")
    def health():
        return jsonify(status="ok")

    # --- Root redirect -------------------------------------------------------
    @app.route("/", methods=["GET", "HEAD"])
    def _root():
        # Prefer an auth login endpoint if present; otherwise land on /health
        target = _try_url_for("auth.login", "/health")
        return redirect(target, code=302)

    # Example: DB ping route (optional for quick DB sanity)
    @app.get("/db-ping")
    def db_ping():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify(db="ok")
        except Exception as e:
            return jsonify(db="error", error=str(e)), 500

    return app
