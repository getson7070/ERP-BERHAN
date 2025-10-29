import os, json
from flask import Flask
from .extensions import db, migrate, csrf, login_manager
from .security import apply_security

try:
    from .ext.limiter import install_limiter
except Exception:
    install_limiter = lambda app: None

def _getenv(key: str, default=None):
    return os.environ.get(key, default)

def _register_optional(app: Flask, import_path: str, *, url_prefix: str | None = None, attr: str = "bp") -> None:
    try:
        mod = __import__(import_path, fromlist=[attr])
        bp = getattr(mod, attr)
        app.register_blueprint(bp, url_prefix=url_prefix)
        app.logger.info("Registered %s as %s", import_path, (bp.url_prefix or url_prefix or ""))
    except Exception as e:
        app.logger.warning("Optional blueprint %s skipped: %s", import_path, e)

def _register_from_explicit(app: Flask) -> int:
    """Register blueprints from a curated allowlist file `erp/blueprints_explicit.py` if present.
    The file should expose: ALLOWLIST = [("erp.web", "/"), ("erp.inventory", "/inventory"), ...]
    Returns number of registered BPs.
    """
    try:
        from .blueprints_explicit import ALLOWLIST  # type: ignore
    except Exception:
        ALLOWLIST = [
            ("erp.web", "/"),
            ("erp.finance", "/finance"),
            ("erp.crm", "/crm"),
            ("erp.sales", "/sales"),
        ]
    count = 0
    for import_path, prefix in ALLOWLIST:
        _register_optional(app, import_path, url_prefix=prefix)
        count += 1
    return count

def create_app() -> Flask:
    app = Flask(__name__)

    # Base config
    app.config.setdefault("SECRET_KEY", _getenv("SECRET_KEY", "dev-insecure"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", _getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///local.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    try: csrf.init_app(app)
    except Exception as e: app.logger.warning("CSRF init skipped: %s", e)
    try: login_manager.init_app(app)
    except Exception as e: app.logger.warning("LoginManager init skipped: %s", e)

    # Security & limiter
    try: apply_security(app)
    except Exception as e: app.logger.info("Security baseline skipped: %s", e)
    try: install_limiter(app)
    except Exception as e: app.logger.info("Limiter install skipped: %s", e)

    # Registration mode
    auto = (_getenv("ERP_AUTO_REGISTER", "0") or "").lower() in {"1","true","yes","on"}
    if auto:
        try:
            from .auto_blueprints import register_all_unique, write_discovery_snapshot
            registered, collisions = register_all_unique(app, pkgs=("erp",))
            write_discovery_snapshot(app, registered)
            app.logger.info("Auto-registered %d blueprints; resolved %d prefix collisions", len(registered), len(collisions))
        except Exception as e:
            app.logger.warning("Auto-registration failed: %s", e)
            # fall back to explicit
            _register_from_explicit(app)
    else:
        _register_from_explicit(app)

    @app.get("/healthz")
    def _healthz():
        return {"ok": True}, 200

    return app

__all__ = ["create_app", "db"]
