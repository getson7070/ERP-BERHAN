import os
from flask import Flask, jsonify
from .extensions import socketio, db, migrate
from .config import Settings
from .capabilities import choose_async_mode, maybe_init_sentry
from .web import web_bp  # new blueprint for pages


def create_app() -> Flask:
    s = Settings()

    app = Flask(
        __name__,
        static_folder="static",        # erp/static
        template_folder="templates",   # erp/templates
    )
    app.config["JSON_SORT_KEYS"] = False

    # ---- DB wiring (kept, optional by env) ----
    if s.DATABASE_URL:
        app.config["SQLALCHEMY_DATABASE_URI"] = s.DATABASE_URL
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        migrate.init_app(app, db)

    # ---- Observability (no-op unless enabled) ----
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

    # ---- Health endpoints (don’t shadow UI) ----
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

    # ---- Register UI/pages ----
    app.register_blueprint(web_bp)

    # ---- Optional: run migrations at startup (off by default) ----
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
