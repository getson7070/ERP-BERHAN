import os
import importlib
from flask import Flask

def _init_extensions(app: Flask) -> None:
    """Initialize extensions in a tolerant way."""
    try:
        from .extensions import db  # type: ignore
        db.init_app(app)
        try:
            from .extensions import migrate  # type: ignore
            migrate.init_app(app, db)
        except Exception:
            app.logger.debug("Flask-Migrate not available or failed to init.", exc_info=True)
    except Exception:
        app.logger.debug("SQLAlchemy 'db' not available or failed to init.", exc_info=True)

    try:
        from .extensions import cache  # type: ignore
        cache.init_app(app)
    except Exception:
        app.logger.debug("Cache not available or failed to init.", exc_info=True)

def _register_blueprint(app: Flask, dotted_path: str) -> None:
    """
    Import a blueprint module/package and register one of several common attributes.
    Never raises; logs and continues on failure.
    """
    try:
        module = importlib.import_module(dotted_path)
        attr_candidates = (
            "bp", "blueprint",
            "ops_bp", "device_bp", "finance_bp", "integration_bp",
            "recall_bp", "bots_bp", "login_bp", "telegram_bp", "health_bp",
        )
        for name in attr_candidates:
            bp = getattr(module, name, None)
            if bp is not None:
                app.register_blueprint(bp)
                try:
                    bp_name = getattr(bp, "name", str(bp))
                except Exception:
                    bp_name = str(bp)
                app.logger.info("Registered blueprint %s from %s", bp_name, dotted_path)
                return
        app.logger.warning("No blueprint attribute found in %s (tried %s)", dotted_path, attr_candidates)
    except Exception:
        app.logger.exception("Failed to register blueprint %s", dotted_path)

def _register_all_blueprints(app: Flask) -> None:
    """Declare blueprints centrally. Missing or broken modules are tolerated."""
    blueprints = [
        "erp.blueprints.health",
        "erp.blueprints.login_ui",          # if you add one later, this will auto-register
        "erp.blueprints.device_trust",
        "erp.blueprints.integration",
        "erp.blueprints.telegram_webhook",
        "erp.blueprints.bots",
        "erp.blueprints.recall",
        "erp.blueprints.finance",
    ]
    for dotted in blueprints:
        _register_blueprint(app, dotted)

def create_app() -> Flask:
    app = Flask(__name__)
    cfg_env = os.getenv("ERP_SETTINGS")
    if cfg_env:
        app.config.from_envvar("ERP_SETTINGS", silent=True)

    _init_extensions(app)

    if os.getenv("ERP_SKIP_BLUEPRINTS") == "1":
        app.logger.info("ERP_SKIP_BLUEPRINTS=1 -> skipping blueprint registration.")
        return app

    _register_all_blueprints(app)
    return app
