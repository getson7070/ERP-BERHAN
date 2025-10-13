# erp/__init__.py
from __future__ import annotations
import importlib
import pkgutil
from datetime import datetime
from flask import Flask, render_template
from .config import Config
from .extensions import init_extensions, db

def _register_blueprints(app: Flask) -> None:
    """Auto-register any blueprint defined as `bp = Blueprint(...)` inside erp.routes.*"""
    import erp.routes as routes_pkg
    for _, module_name, is_pkg in pkgutil.iter_modules(routes_pkg.__path__):
        if is_pkg:
            continue
        module_fqn = f"{routes_pkg.__name__}.{module_name}"
        module = importlib.import_module(module_fqn)
        bp = getattr(module, "bp", None) or getattr(module, "main_bp", None)
        if bp is not None:
            app.register_blueprint(bp)

def _register_error_pages(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

def _inject_brand_context(app: Flask) -> None:
    @app.context_processor
    def inject():
        return {
            "brand_name": app.config.get("BRAND_NAME", "BERHAN"),
            "brand_logo_path": app.config.get("BRAND_LOGO_PATH", "pictures/BERHAN-PHARMA-LOGO.jpg"),
            "brand_primary": app.config.get("BRAND_PRIMARY", "#1e88e5"),
            "brand_accent": app.config.get("BRAND_ACCENT", "#00acc1"),
            "current_year": datetime.utcnow().year,
        }

def _ensure_tables(app: Flask) -> None:
    # Safe for SQLite fallback; for Postgres + Alembic, you still run alembic migrations in CI/CD
    with app.app_context():
        db.create_all()

def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object or Config)

    init_extensions(app)
    _inject_brand_context(app)
    _register_blueprints(app)
    _register_error_pages(app)
    _ensure_tables(app)  # ensures boot does not crash if DB env missing

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
