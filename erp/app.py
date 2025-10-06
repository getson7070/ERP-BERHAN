# erp/app.py
import os
from pathlib import Path
from flask import Flask
from .extensions import init_extensions, login_manager, db

def _detect_paths():
    """Prefer project-root /templates and /static if present; otherwise use erp/…"""
    here = Path(__file__).resolve().parent        # …/erp
    project_root = here.parent                    # repo root
    templates = (project_root / "templates") if (project_root / "templates").is_dir() else (here / "templates")
    static = (project_root / "static") if (project_root / "static").is_dir() else (here / "static")
    return str(templates), str(static)

def create_app(config_name: str | None = None):
    template_dir, static_dir = _detect_paths()

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=template_dir,
        static_folder=static_dir,
    )

    # ---- Core config
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev")

    db_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("Database URL missing. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL.")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---- Mail (safe defaults; override via env on Render/.env locally)
    app.config.setdefault("MAIL_SERVER", os.getenv("MAIL_SERVER", "localhost"))
    app.config.setdefault("MAIL_PORT", int(os.getenv("MAIL_PORT", "25")))
    app.config.setdefault("MAIL_USE_TLS", os.getenv("MAIL_USE_TLS", "false").lower() == "true")
    app.config.setdefault("MAIL_USERNAME", os.getenv("MAIL_USERNAME"))
    app.config.setdefault("MAIL_PASSWORD", os.getenv("MAIL_PASSWORD"))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER"))

    # Optional Socket.IO queue (Redis)
    app.config.setdefault("SOCKETIO_MESSAGE_QUEUE", os.getenv("SOCKETIO_REDIS_URL"))

    # ---- Init all extensions (db/migrate/cache/limiter/login/mail/socketio)
    init_extensions(app)

    # ---- Flask-Login user loader (lazy import to avoid circulars)
    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            from .models import User  # imported only when needed
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # ---- Blueprints
    from .web import web_bp
    from .routes.auth import auth_bp
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # ---- Health
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
