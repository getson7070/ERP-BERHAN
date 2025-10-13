# erp/__init__.py — deterministic blueprint registration
from __future__ import annotations
import logging
from flask import Flask, render_template
from .extensions import init_extensions

logger = logging.getLogger("erp")

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_prefixed_env()  # APP_/FLASK_

    init_extensions(app)

    # Error pages
    @app.errorhandler(404)
    def not_found(e):
        try:
            return render_template("errors/404.html"), 404
        except Exception:
            return "Not Found", 404

    @app.errorhandler(500)
    def internal(e):
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            return "Server Error", 500

    # Explicit, safe blueprint registration
    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    # Auth
    try:
        from .routes.auth import bp as auth_bp
    except Exception:
        from .routes.auth import bp as auth_bp  # keep alias; fail loudly if missing
    app.register_blueprint(auth_bp)

    # Core UI routes (safe if files exist)
    def _try_register(path, name):
        try:
            mod = __import__(path, fromlist=[name])
            bp = getattr(mod, name, None)
            if bp is not None:
                app.register_blueprint(bp)
                logger.info("Registered blueprint %s.%s", path, name)
        except Exception as ex:
            logger.warning("Skipped blueprint %s.%s: %s", path, name, ex)

    _try_register("erp.routes.inventory", "bp")           # UI list page
    _try_register("erp.routes.receive_inventory", "bp")   # QR/receiving
    _try_register("erp.finance.routes", "finance_bp")     # API finance
    _try_register("erp.inventory.routes", "inventory_bp") # API inventory
    _try_register("erp.procurement.routes", "proc_bp")    # API procurement
    _try_register("erp.sales.routes", "sales_bp")         # API sales
    _try_register("erp.routes.hr", "bp")
    _try_register("erp.routes.hr_workflows", "bp")
    _try_register("erp.routes.crm", "bp")
    _try_register("erp.routes.analytics", "bp")
    _try_register("erp.routes.admin", "bp")
    _try_register("erp.routes.projects", "bp")
    _try_register("erp.routes.report_builder", "bp")
    _try_register("erp.routes.tenders", "bp")
    _try_register("erp.routes.plugins", "bp")

    return app
