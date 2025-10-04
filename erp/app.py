import os
from flask import Flask, jsonify
from .extensions import socketio, db, migrate
from .config import Settings
from .capabilities import choose_async_mode, maybe_init_sentry

def create_app() -> Flask:
    s = Settings()  # read env & defaults once

    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # --- DB wiring (kept even if you don't use migrations today) ---
    if s.DATABASE_URL:
        app.config["SQLALCHEMY_DATABASE_URI"] = s.DATABASE_URL
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        migrate.init_app(app, db)

    # --- Observability (no-op unless enabled & DSN provided) ---
    maybe_init_sentry(s)

    # --- Socket.IO progressive init ---
    async_mode = choose_async_mode(s)
    socketio.init_app(
        app,
        async_mode=async_mode,
        cors_allowed_origins="*",
        message_queue=s.SOCKETIO_MESSAGE_QUEUE or None,  # enables multi-instance scaling when set
    )
    try:
        app.logger.info(f"Flask-SocketIO async_mode: {async_mode}")
    except Exception:
        pass

    # --- Minimal health & readiness ---
    @app.get("/")
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

    # --- Optional: auto-migrate on startup (safe off by default) ---
    if s.MIGRATE_ON_STARTUP and s.DATABASE_URL:
        _safe_upgrade_head(app)

    # --- register blueprints lazily here (kept minimal for now) ---
    # from .api import api_bp
    # app.register_blueprint(api_bp, url_prefix="/api")

    return app


def _safe_upgrade_head(app: Flask):
    """
    Run Alembic migrations at startup when MIGRATE_ON_STARTUP=1 is set.
    Fails soft (logs) so the app can still boot in degraded mode if DB is not ready.
    """
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command

        # looks for alembic.ini at repo root; adjust if yours lives elsewhere
        cfg_path = os.getenv("ALEMBIC_INI", "alembic.ini")
        cfg = AlembicConfig(cfg_path)
        alembic_command.upgrade(cfg, "head")
        app.logger.info("Startup migration: upgrade to head completed.")
    except Exception as exc:
        app.logger.warning(f"Startup migration skipped or failed: {exc}")
