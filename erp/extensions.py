# erp/extensions.py
"""
Centralize extension instances and app wiring.
- Provides a safety Flask-Login loader so public pages never 500.
- Registers all UI blueprints (fixes /auth/login 404).
"""

from __future__ import annotations
import os
from typing import Optional, Callable

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_socketio import SocketIO

# ----- Extension instances -----
db = SQLAlchemy(session_options={"autoflush": False})
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cors = CORS()
mail = Mail()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})  # swap to Redis in prod
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")  # tighten in prod

# Limiter (use Redis in prod)
def _limiter_factory(app: Flask):
    storage_uri = os.getenv("LIMITER_STORAGE_URI")  # e.g. redis://:pass@host:port/0
    if storage_uri:
        return Limiter(key_func=get_remote_address, storage_uri=storage_uri)
    # in-memory warning is acceptable for dev
    return Limiter(key_func=get_remote_address)

limiter: Optional[Limiter] = None

__safety_loader_bound = False


def init_extensions(app: Flask) -> None:
    global limiter

    # Database URI from env (Render Postgres)
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///local.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Mail (optional)
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER", "noreply@example.com"))

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    csrf.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

    cache.init_app(app)
    mail.init_app(app)

    limiter = _limiter_factory(app)
    limiter.init_app(app)

    socketio.init_app(app)

    class _Anon(AnonymousUserMixin):
        @property
        def is_admin(self): return False
        @property
        def roles(self): return []
        name = "Guest"
        email = None

    login_manager.anonymous_user = _Anon


def register_safety_login_loader() -> None:
    """
    Register a no-op user_loader so templates can always access `current_user`
    without Flask-Login raising "Missing user_loader or request_loader".
    Your real loader (once your User model is ready) can override this safely.
    """
    global __safety_loader_bound
    if __safety_loader_bound:
        return

    @login_manager.user_loader
    def _safe_loader(_user_id: str):
        return None  # Anonymous

    __safety_loader_bound = True


def register_common_blueprints(app: Flask) -> None:
    """
    Register all UI/API blueprints that exist in erp/routes/.
    This fixes 404s like /auth/login and ensures the nav works.
    """
    # Import locally to avoid circular imports
    from .routes.main import bp as main_bp
    from .routes.auth import auth_bp
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
    from .routes.api import api_bp
    from .routes.webhooks import bp as webhooks_bp

    # Public first, then the rest
    app.register_blueprint(main_bp)
    app.register_blueprint(help_bp)
    app.register_blueprint(privacy_bp)

    # Auth
    app.register_blueprint(auth_bp)

    # Core modules
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

    # API/Webhooks last
    app.register_blueprint(api_bp)
    app.register_blueprint(webhooks_bp)
