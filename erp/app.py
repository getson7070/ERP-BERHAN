import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader
from .extensions import socketio, db, migrate
from .config import Settings
from .capabilities import choose_async_mode, maybe_init_sentry
from .web import web_bp  # UI blueprint (routes for /, /login, /dashboard)

def create_app() -> Flask:
    s = Settings()

    # Package and repo layout
    pkg_root = Path(__file__).resolve().parent       # .../erp
    repo_root = pkg_root.parent                      # repo root

    app = Flask(__name__)  # don't fix template_folder here; we will set loaders
    app.config["JSON_SORT_KEYS"] = False
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me-now")

    # ---- Jinja template search order ----
    # 1) <repo>/templates  (PRIMARY, as you requested)
    # 2) <repo>/erp/templates
    root_templates = repo_root / "templates"
    erp_templates = pkg_root / "templates"
    loaders = []
    if root_templates.is_dir():
        loaders.append(FileSystemLoader(str(root_templates)))
    # include default loader if any (so Flask's package templates remain usable)
    loaders.append(FileSystemLoader(str(erp_templates)))
    app.jinja_loader = ChoiceLoader(loaders)

    # ---- Static files ----
    # primary static at <repo>/static, but also expose erp/static as /erp-static/...
    root_static = repo_root / "static"
    if root_static.is_dir():
        app.static_folder = str(root_static)
        app.static_url_path = "/static"
    erp_static = pkg_root / "static"
    if erp_static.is_dir():
        @app.route("/erp-static/<path:filename>")
        def _erp_static(filename):
            return send_from_directory(str(erp_static), filename)

    # ---- DB wiring (optional by env) ----
    if s.DATABASE_URL:
        app.config["SQLALCHEMY_DATABASE_URI"] = s.DATABASE_URL
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        migrate.init_app(app, db)

    # ---- Observability (optional) ----
    maybe_init_sentry(s)

    # ---- Socket.IO progressive init ----
    async_mode = choose_async_mode(s)
    socketio.init_app(
        app,
        async_mode=async_mode,
        cors_allowed_origins="*",
        message_queue=s.SOCKETIO_MESSAGE_QUEUE or None,
    )
    try:
        app.logger.info(f"Flask-SocketIO async_mode: {async_mode}")
    except Exception:
        pass

    # ---- Health endpoints ----
    @app.get("/health")
    def health():
        return jsonify({"app": "ERP-BERHAN", "status": "running"})

    @app.get("/ready")
    def ready():
        return jsonify({
            "socketio": async_mode,
            "db": bool(s.DATABASE_URL),
            "observability": bool(s.SENTRY_DSN) and s.ENABLE_OBSERVABILITY,
            "auto_migrate": bool(s.MIGRATE_ON_STARTUP),
        })

    # ---- UI routes ----
    app.register_blueprint(web_bp)

    # ---- Optional startup migrations ----
    if s.MIGRATE_ON_STARTUP and s.DATABASE_URL:
        _safe_upgrade_head(app)

    return app


def _safe_upgrade_head(app: Flask):
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command
        cfg_path = os.getenv("ALEMBIC_INI", "alembic.ini")
        cfg = AlembicConfig(cfg_path)
        alembic_command.upgrade(cfg, "head")
        app.logger.info("Startup migration: upgrade to head completed.")
    except Exception as exc:
        app.logger.warning(f"Startup migration skipped or failed: {exc}")
