from __future__ import annotations

import importlib
import importlib.util
import logging
import os
from typing import Iterable

from flask import Blueprint as FlaskBlueprint, Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import init_extensions
from .errors import register_error_handlers
from .security import apply_security
from .middleware.security_headers import apply_security_headers
from .middleware.tenant_guard import install_tenant_guard
from .security_gate import install_global_gate

LOGGER = logging.getLogger(__name__)


def _load_config(app: Flask) -> None:
    ERPConfig = None
    if importlib.util.find_spec("erp.config"):
        from erp.config import Config as ERPConfig  # type: ignore

    if ERPConfig is not None:
        app.config.from_object(ERPConfig)
        return

    secret_key = os.environ.get("SECRET_KEY", "change-me")
    database_url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("SQLALCHEMY_DATABASE_URI")
        or "sqlite:///local.db"
    )

    app.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PORT=int(os.environ.get("PORT", "18000")),
    )


def _discover_blueprints() -> list[tuple[str, FlaskBlueprint]]:
    candidates = [
        # UI / core
        "erp.routes.main:main_bp",
        "erp.routes.auth:auth_bp",
        "erp.routes.health:health_bp",
        "erp.routes.orgs:orgs_bp",
        "erp.routes.users:users_bp",
        "erp.routes.rbac:rbac_bp",
        "erp.routes.audit:audit_bp",
        "erp.routes.orders:bp",
        "erp.routes.inventory:inventory_bp",
        "erp.routes.maintenance:maintenance_bp",
        "erp.routes.reports:reports_bp",
        "erp.routes.admin:bp",

        # API
        "erp.routes.api:bp",
        "erp.routes.admin_console_api:bp",
        "erp.routes.client_auth_api:bp",
        "erp.routes.client_portal:bp",
        "erp.routes.analytics_dashboard_api:bp",
        "erp.routes.banking_api:bp",
        "erp.routes.audit_api:bp",
        "erp.routes.crm_api:bp",

        # NEW (C3)
        "erp.routes.commissions_api:bp",
    ]

    out: list[tuple[str, FlaskBlueprint]] = []
    for spec in candidates:
        mod_name, obj_name = spec.split(":")
        try:
            mod = importlib.import_module(mod_name)
            obj = getattr(mod, obj_name, None)
            if isinstance(obj, FlaskBlueprint):
                out.append((spec, obj))
        except Exception as e:
            LOGGER.warning("Skipping blueprint %s: %s", spec, e)
    return out


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    _load_config(app)
    init_extensions(app)

    apply_security(app)
    apply_security_headers(app)
    install_tenant_guard(app)
    install_global_gate(app)

    register_error_handlers(app)

    for spec, bp in _discover_blueprints():
        try:
            app.register_blueprint(bp)
        except Exception as e:
            LOGGER.error("Failed to register %s: %s", spec, e)

    return app


__all__ = ["create_app"]
