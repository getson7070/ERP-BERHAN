# erp/extensions.py
from __future__ import annotations
import os
from typing import Callable
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_cors import CORS

# --- Singletons (defined at import time, never None) ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
mail = Mail()
limiter = Limiter(key_func=get_remote_address)  # always a real object
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_extensions(app: Flask) -> None:
    # Core app defaults
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("PREFERRED_URL_SCHEME", "https")
    app.config.setdefault("RATELIMIT_ENABLED", True)

    # Wire up CORS (adjust origins as needed)
    CORS(app, resources={r"*": {"origins": "*"}})

    # Prefer Redis if provided
    redis_url = os.getenv("REDIS_URL") or os.getenv("RATELIMIT_STORAGE_URI")
    if redis_url:
        app.config["SOCKETIO_MESSAGE_QUEUE"] = redis_url

    # Initialize
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

def register_safety_login_loader() -> None:
    # Ensure public pages never 500 if no user is logged in
    class _Anon(AnonymousUserMixin):
        @property
        def is_admin(self): return False
        @property
        def roles(self): return []
        name = "Guest"
        email = None
    login_manager.anonymous_user = _Anon  # type: ignore

def register_common_blueprints(app: Flask) -> None:
    # Import inside function to avoid import-time side effects
    from .routes.main import bp as main_bp
    from .routes.auth import auth_bp
    from .routes.api import api_bp
    from .routes.orders import bp as orders_bp
    from .routes.tenders import bp as tenders_bp
    from .routes.inventory import bp as inventory_bp
    from .routes.receive_inventory import bp as receive_inventory_bp
    from .routes.procurement import bp as procurement_bp
    from .routes.finance import bp as finance_bp
    from .routes.hr import bp as hr_bp
    from .routes.hr_workflows import hr_workflows_bp
    from .routes.projects import bp as projects_bp
    from .routes.manufacturing import bp as manufacturing_bp
    from .routes.plugins import bp as plugins_bp
    from .routes.crm import bp as crm_bp
    from .routes.report_builder import reports_bp
    from .routes.dashboard_customize import bp as dashboard_customize_bp
    from .routes.kanban import bp as kanban_bp
    from .routes.admin import bp as admin_bp
    from .routes.help import bp as help_bp
    from .routes.privacy import bp as privacy_bp
    from .routes.feedback import bp as feedback_bp
    from .routes.health import bp as health_bp
    from .routes.analytics import bp as analytics_bp
    from .routes.webhooks import webhooks_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(tenders_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(receive_inventory_bp)
    app.register_blueprint(procurement_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(hr_workflows_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(manufacturing_bp)
    app.register_blueprint(plugins_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(dashboard_customize_bp)
    app.register_blueprint(kanban_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(help_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(webhooks_bp)
