# erp/app.py
import os
import importlib
from typing import Iterable
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

def _register_blueprint(app: Flask, dotted_path: str, attr_candidates: Iterable[str] = ("bp", "ops_bp")):
    """
    Import a module and register its blueprint. Accepts multiple attribute names
    to avoid fragile renames (e.g., bp vs ops_bp). Raises loudly on failure.
    """
    module = importlib.import_module(dotted_path)
    bp = None
    for name in attr_candidates:
        if hasattr(module, name):
            bp = getattr(module, name)
            break
    if bp is None:
        raise RuntimeError(f"{dotted_path} exports no blueprint named any of {attr_candidates}")
    app.register_blueprint(bp)
    app.logger.info("Registered blueprint %s from %s", getattr(bp, "name", bp), dotted_path)

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Basic config
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-not-secure"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "postgresql+psycopg://erp:erp@db:5432/erp"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        REDIS_URL=os.getenv("REDIS_URL", "redis://cache:6379/0"),
        PREFERRED_URL_SCHEME=os.getenv("URL_SCHEME", "http"),
        JSON_SORT_KEYS=False,
    )

    # Allow instance config override if present
    cfg_obj = os.getenv("FLASK_CONFIG_OBJECT")
    if cfg_obj:
        app.config.from_object(cfg_obj)

    # Proxy fix for running behind reverse proxies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Minimal health endpoints (no DB touch)
    @app.get("/health")
    @app.get("/healthz")
    def health():
        return jsonify({"ok": True, "service": "erp"})

    # Register blueprints (fail fast; don’t hide errors)
    blueprints = [
        "erp.ops.status",
        "erp.ops.doctor",         # exports ops_bp in your repo; importer accepts bp/ops_bp
        "erp.auth.mfa_routes",
        # domain blueprints; importer tolerates absence
        "erp.blueprints.finance",
        "erp.blueprints.integration",
        "erp.blueprints.recall",
        "erp.blueprints.bots",
        "erp.blueprints.device_trust",
        "erp.blueprints.login_ui",
        "erp.routes.report_builder",
        "erp.blueprints.telegram_webhook",
        "erp.blueprints.admin_devices",
    ]
    for dotted in blueprints:
        try:
            _register_blueprint(app, dotted)
        except ModuleNotFoundError:
            app.logger.info("Optional blueprint %s not present; skipping.", dotted)
        except Exception as e:
            # Loud by default – this shouldn’t be silenced in production
            app.logger.exception("Failed to register blueprint %s: %s", dotted, e)
            raise

    # Optional LAN gate middleware
    try:
        from erp.middleware.lan_gate import block_non_lan_for_sensitive_paths
        block_non_lan_for_sensitive_paths(app)
    except Exception as e:
        app.logger.info("LAN gate not active: %s", e)

    return app

app = create_app()

if __name__ == "__main__":
    # dev server
    app.run(host="0.0.0.0", port=5000, debug=True)


