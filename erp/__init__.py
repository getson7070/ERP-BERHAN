"""ERP package root.

This package bundles the various modules of the ERP-BERHAN system, including
finance, CRM, sales, user management and core data models.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Iterable

import sentry_sdk
from flask import Blueprint as FlaskBlueprint, Flask, jsonify
from flask_login import current_user
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.middleware.proxy_fix import ProxyFix

from db import redis_client  # type: ignore

from .db import db as db
from .dlq import _dead_letter_handler
from .extensions import cache, init_extensions, limiter, login_manager, mail
from .logging_setup import setup_json_logging
from .errors import register_error_handlers
from .metrics import (
    AUDIT_CHAIN_BROKEN,
    DLQ_MESSAGES,
    GRAPHQL_REJECTS,
    QUEUE_LAG,
    RATE_LIMIT_REJECTIONS,
    RATE_LIMIT_REJECTIONS,
)
from .middleware.security_headers import apply_security_headers
from .middleware.tenant_guard import install_tenant_guard
from .bots.registry import register_default_bot_commands
from .security import apply_security, install_privileged_mfa_guard
from .security_gate import install_global_gate
from .socket import socketio

from .menu import build_menu_for_user

LOGGER = logging.getLogger(__name__)


def _parse_service_tokens(raw: str) -> dict[str, tuple[str, ...]]:
    tokens: dict[str, tuple[str, ...]] = {}
    if not raw:
        return tokens
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        token, roles_raw = chunk.split(":", 1)
        token = token.strip()
        roles = tuple(
            sorted(
                {
                    role.strip().lower()
                    for role in roles_raw.replace("|", ",").split(",")
                    if role.strip()
                }
            )
        )
        if token and roles:
            tokens[token] = roles
    return tokens


def _load_config(app: Flask) -> None:
    ERPConfig = None
    if importlib.util.find_spec("erp.config"):
        from erp.config import Config as ERPConfig  # type: ignore

    if ERPConfig is not None:
        app.config.from_object(ERPConfig)
        return

    InstanceConfig = None
    if importlib.util.find_spec("config"):
        from config import Config as InstanceConfig  # type: ignore

    if InstanceConfig is not None:
        app.config.from_object(InstanceConfig)
        return

    allow_insecure = os.environ.get("ALLOW_INSECURE_DEFAULTS") == "1"
    if os.environ.get("FLASK_ENV") == "development":
        allow_insecure = True

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key or secret_key == "change-me":
        if allow_insecure:
            secret_key = secret_key or "change-me"
        else:
            raise RuntimeError(
                "SECRET_KEY is not configured. Export SECRET_KEY or set "
                "ALLOW_INSECURE_DEFAULTS=1 for ephemeral local testing."
            )

    database_url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("SQLALCHEMY_DATABASE_URI")
        or ""
    )
    if not database_url:
        database_path = os.environ.get("DATABASE_PATH")
        if database_path:
            database_url = f"sqlite:///{database_path}"
        elif allow_insecure:
            database_url = "sqlite:///local.db"
        else:
            raise RuntimeError(
                "DATABASE_URL / SQLALCHEMY_DATABASE_URI not configured."
            )

    app.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        REDIS_URL=os.environ.get("REDIS_URL", ""),
        PORT=int(os.environ.get("PORT", "18000")),
        SERVICE_TOKENS=_parse_service_tokens(os.environ.get("SERVICE_TOKENS", "")),
    )


def _install_sentry(app: Flask) -> None:
    dsn = app.config.get("SENTRY_DSN") or os.environ.get("SENTRY_DSN")
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=float(app.config.get("SENTRY_TRACES_SAMPLE_RATE", 0.0)),
        environment=os.environ.get("SENTRY_ENVIRONMENT", os.environ.get("FLASK_ENV", "production")),
    )


def _discover_blueprints() -> list[tuple[str, FlaskBlueprint]]:
    """
    Keep blueprint discovery conservative. If a module is missing,
    skip it instead of killing the server.

    IMPORTANT:
    - Register both UI and API blueprints that the system depends on.
    - Client onboarding (C2) requires client_auth_api + admin_console_api to be registered.
    """
    candidates = [
        # UI / core
        "erp.routes.main:main_bp",
        "erp.routes.auth:auth_bp",
        "erp.routes.health:health_bp",
        "erp.routes.orgs:orgs_bp",
        "erp.routes.users:users_bp",
        "erp.routes.rbac:rbac_bp",
        "erp.routes.audit:audit_bp",
        "erp.routes.orders:orders_bp",
        "erp.routes.inventory:inventory_bp",
        "erp.routes.maintenance:maintenance_bp",
        "erp.routes.reports:reports_bp",

        # API (needed for dashboards + bots + onboarding)
        "erp.routes.api:bp",
        "erp.routes.admin_console_api:bp",
        "erp.routes.client_auth_api:bp",
        "erp.routes.client_portal:bp",

        # Keep adding your other APIs here as needed:
        # "erp.routes.maintenance_api:bp",
        # "erp.routes.inventory_ext_api:bp",
        # "erp.routes.geo_api:bp",
        # "erp.routes.analytics_api:bp",
        # "erp.routes.crm_api:bp",
    ]

    out: list[tuple[str, FlaskBlueprint]] = []
    for spec in candidates:
        mod_name, obj_name = spec.split(":")
        try:
            mod = importlib.import_module(mod_name)
            bp = getattr(mod, obj_name, None)
            if isinstance(bp, FlaskBlueprint):
                out.append((spec, bp))
        except Exception as e:
            LOGGER.warning("Skipping blueprint %s: %s", spec, e)
    return out


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    _load_config(app)
    setup_json_logging(app)
    _install_sentry(app)

    init_extensions(app)

    # Security + guards
    apply_security(app)
    apply_security_headers(app)
    install_tenant_guard(app)
    install_global_gate(app)
    install_privileged_mfa_guard(app)

    # Error handlers
    register_error_handlers(app)

    # Blueprints
    for spec, bp in _discover_blueprints():
        try:
            app.register_blueprint(bp)
        except Exception as e:
            LOGGER.error("Failed to register %s: %s", spec, e)

    # SocketIO
    try:
        socketio.init_app(app)
    except Exception as e:
        LOGGER.warning("SocketIO init skipped: %s", e)

    # Bots
    try:
        register_default_bot_commands(app)
    except Exception as e:
        LOGGER.warning("Bot registry skipped: %s", e)

    # DLQ
    try:
        _dead_letter_handler(app)
    except Exception as e:
        LOGGER.warning("DLQ handler skipped: %s", e)

    # Optional: expose menu build for templates
    try:
        @app.context_processor
        def inject_menu():
            if getattr(current_user, "is_authenticated", False):
                return {"menu": build_menu_for_user(current_user)}
            return {"menu": []}
    except Exception:
        pass

    return app


__all__ = ["create_app", "db"]
