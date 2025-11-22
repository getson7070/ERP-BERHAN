"""ERP package root.

This package bundles the various modules of the ERP‑BERHAN system, including
finance, CRM, sales, user management and core data models. The modules are
organised into subpackages with clearly defined responsibilities. See the
documentation for details on each module’s functionality.
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

from flask import Blueprint as FlaskBlueprint, Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from db import redis_client  # type: ignore

from .db import db as db
from .dlq import _dead_letter_handler
from .extensions import cache, init_extensions, limiter, login_manager, mail
from .metrics import (
    AUDIT_CHAIN_BROKEN,
    DLQ_MESSAGES,
    GRAPHQL_REJECTS,
    QUEUE_LAG,
    RATE_LIMIT_REJECTIONS,
)
from .socket import socketio
from .middleware.security_headers import apply_security_headers
from .security import apply_security
from .security_gate import install_global_gate
from .middleware.tenant_guard import install_tenant_guard

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

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
    """Populate ``app.config`` from the canonical Config object or env vars."""

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
        else:  # Production/staging must explicitly configure a secret
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
                "DATABASE_URL is not configured. Set DATABASE_URL/SQLALCHEMY_DATABASE_URI "
                "or opt in to ALLOW_INSECURE_DEFAULTS=1 for disposable dev runs."
            )

    raw_roles = os.environ.get("SELF_REGISTRATION_ALLOWED_ROLES", "employee,client")
    allowed_roles = tuple(
        sorted({role.strip().lower() for role in raw_roles.split(",") if role.strip()})
    )

    strict_org_boundaries = os.environ.get("STRICT_ORG_BOUNDARIES", "1") != "0"
    default_org_id = int(os.environ.get("DEFAULT_ORG_ID", 1))
    service_tokens = _parse_service_tokens(os.environ.get("SERVICE_TOKENS", ""))

    automation_roles = tuple(
        sorted(
            {
                role.strip().lower()
                for role in os.environ.get("AUTOMATION_MACHINE_ROLES", "automation").split(",")
                if role.strip()
            }
        )
    ) or ("automation",)

    ldap_group_role_map = os.environ.get("LDAP_GROUP_ROLE_MAP_JSON", "{}")

    ldap_enabled = os.environ.get("LDAP_ENABLED", "0") == "1"
    ldap_url = os.environ.get("LDAP_URL")
    ldap_base_dn = os.environ.get("LDAP_BASE_DN")
    ldap_bind_dn = os.environ.get("LDAP_BIND_DN")
    ldap_bind_password = os.environ.get("LDAP_BIND_PASSWORD")

    audit_key = os.environ.get("AUDIT_FERNET_KEY")
    if not audit_key:
        seed = secret_key or os.environ.get("AUDIT_FALLBACK_SEED", "")
        digest = hashlib.sha256(str(seed).encode()).digest()
        audit_key = base64.urlsafe_b64encode(digest).decode()

    app.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Sensible defaults to avoid dev-time warnings while still keeping
        # security-focused settings (short-lived, in-memory cache by default).
        CACHE_TYPE=os.environ.get("CACHE_TYPE", "SimpleCache"),
        CACHE_DEFAULT_TIMEOUT=int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300)),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        WTF_CSRF_TIME_LIMIT=3600,
        WTF_CSRF_CHECK_DEFAULT=True,
        WTF_CSRF_HEADERS=("X-CSRFToken", "X-CSRF-Token"),
        SELF_REGISTRATION_MODE=os.environ.get("SELF_REGISTRATION_MODE", "invite-only"),
        SELF_REGISTRATION_ALLOWED_ROLES=allowed_roles,
        PRIVILEGED_ROLES=("admin", "owner", "superuser"),
        STRICT_ORG_BOUNDARIES=strict_org_boundaries,
        DEFAULT_ORG_ID=default_org_id,
        SERVICE_TOKEN_MAP=service_tokens,
        AUTOMATION_MACHINE_ROLES=automation_roles,
        AUDIT_FERNET_KEY=audit_key,
        LDAP_ENABLED=ldap_enabled,
        LDAP_URL=ldap_url,
        LDAP_BASE_DN=ldap_base_dn,
        LDAP_BIND_DN=ldap_bind_dn,
        LDAP_BIND_PASSWORD=ldap_bind_password,
        LDAP_GROUP_ROLE_MAP_JSON=ldap_group_role_map,
    )


# ---------------------------------------------------------------------------
# Blueprint discovery
# ---------------------------------------------------------------------------

_MANIFEST = Path(__file__).resolve().parent.parent / "blueprints_dedup_manifest.txt"
_DEFAULT_BLUEPRINT_MODULES = [
    "erp.main",
    "erp.web",
    "erp.views_ui",
    "erp.routes.main",
    "erp.routes.health",
    "erp.routes.dashboard_customize",
    "erp.routes.analytics",
    "erp.routes.auth",
    "erp.routes.banking_api",
    "erp.routes.approvals",
    "erp.routes.maintenance",
    "erp.routes.maintenance_api",
    "erp.routes.orders",
    "erp.routes.projects",
    "erp.routes.manufacturing",
    "erp.sales.routes",
    "erp.marketing.routes",
    "erp.routes.plugins",
    "erp.routes.plugins_sample",
    "erp.routes.inventory",
    "erp.procurement.routes",
    "erp.routes.finance",
    "erp.routes.finance_gl",
    "erp.routes.finance_reconcile",
    "erp.routes.finance_reports",
    "erp.routes.hr",
    "erp.routes.crm",
    "erp.routes.crm_api",
    "erp.routes.performance_api",
    "erp.routes.analytics_api",
    "erp.routes.csrf_api",
    "erp.routes.marketing_api",
    "erp.routes.marketing_geofence",
    "erp.routes.geo_api",
    "erp.routes.client_portal",
    "erp.routes.audit_api",
    "erp.routes.bot_dashboard_api",
    "erp.routes.admin_console_api",
    "erp.routes.sso_oidc",
    "erp.routes.client_auth_api",
    "erp.routes.client_oauth_api",
    "erp.routes.mttr_api",
    "erp.routes.rbac_policy_api",
    "erp.routes.role_request_api",
    "erp.supplychain.routes",
    "erp.routes.report_builder",
    "erp.blueprints.inventory",
    "erp.blueprints.bots",
    "erp.blueprints.telegram_webhook",
]

_EXCLUDED_BLUEPRINT_MODULES = {
    "erp.health_checks",
    "erp.blueprints.health_compat",
    "erp.ops.health",
    "erp.ops.status",
    "erp.finance.banking",  # legacy banking blueprint defining duplicate models
    "erp.crm.routes",  # legacy CRM blueprint colliding with the upgraded module
}


def _iter_blueprint_modules() -> Iterable[str]:
    """Yield dotted module paths that are expected to expose a Blueprint."""

    seen: set[str] = set()

    if _MANIFEST.exists():
        for line in _MANIFEST.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            if line.startswith("CHOSEN") or line.startswith("SKIPPED"):
                continue
            if line.startswith("- "):
                parts = line.split(":", 1)
                if len(parts) != 2:
                    continue
                module = parts[1].strip().split()[0]
                if "." in module:
                    module = module.rsplit(".", 1)[0]
                if module and module not in seen:
                    seen.add(module)
                    yield module

    for module in _DEFAULT_BLUEPRINT_MODULES:
        if module not in seen:
            seen.add(module)
            yield module


def _extract_blueprints(module_obj) -> list[FlaskBlueprint]:
    """Return Blueprint objects exposed by *module_obj* (if any)."""

    discovered: list[FlaskBlueprint] = []
    seen: set[str] = set()
    for attr_name, attr in vars(module_obj).items():
        if isinstance(attr, FlaskBlueprint) and attr.name not in seen:
            seen.add(attr.name)
            discovered.append(attr)
    return discovered


def register_blueprints(app: Flask) -> None:
    """Register all configured blueprints while avoiding duplicates."""

    for module in _iter_blueprint_modules():
        if module in _EXCLUDED_BLUEPRINT_MODULES:
            LOGGER.debug("Skipping excluded blueprint module %s", module)
            continue

        spec = importlib.util.find_spec(module)
        if spec is None:
            LOGGER.warning("Blueprint module %s not found; skipping", module)
            continue

        module_obj = importlib.import_module(module)
        blueprints = _extract_blueprints(module_obj)
        if not blueprints:
            LOGGER.debug("Module %s defines no Blueprint instances", module)
            continue

        for blueprint in blueprints:
            if blueprint.name in app.blueprints:
                LOGGER.debug("Blueprint %s already registered", blueprint.name)
                continue
            app.register_blueprint(blueprint)


def _register_core_routes(app: Flask) -> None:
    routes = {rule.rule for rule in app.url_map.iter_rules()}

    if "/healthz" not in routes:

        @app.get("/healthz")
        def healthz():
            return jsonify(status="ok"), 200


def create_app(config_object: str | None = None) -> Flask:
    """Application factory used by Flask, Celery, and CLI tooling."""

    app = Flask(__name__, instance_relative_config=False)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    if config_object:
        app.config.from_object(config_object)
    else:
        _load_config(app)

    init_extensions(app)
    apply_security(app)
    apply_security_headers(app)
    register_blueprints(app)
    install_global_gate(app)
    install_tenant_guard(app)
    from erp.routes.sso_oidc import init_sso

    init_sso(app)

    # Guarantee marketing endpoints are present even when manifest skips them
    marketing_spec = importlib.util.find_spec("erp.marketing.routes")
    if marketing_spec is not None:
        marketing_routes = importlib.import_module("erp.marketing.routes")
        marketing_bp = getattr(marketing_routes, "bp", None)

        if marketing_bp and "marketing" not in app.blueprints:
            app.register_blueprint(marketing_bp)
        if hasattr(marketing_routes, "visits") and "marketing.visits" not in app.view_functions:
            app.add_url_rule(
                "/marketing/visits",
                endpoint="marketing.visits",
                view_func=marketing_routes.visits,
                methods=["GET", "POST"],
            )
        if hasattr(marketing_routes, "events") and "marketing.events" not in app.view_functions:
            app.add_url_rule(
                "/marketing/events",
                endpoint="marketing.events",
                view_func=marketing_routes.events,
                methods=["GET", "POST"],
            )
    else:
        LOGGER.warning("Marketing blueprint module missing; endpoints not registered")

    _register_core_routes(app)

    # Ensure models are imported for Alembic autogenerate & shell usage.
    models_spec = importlib.util.find_spec("erp.models")
    if models_spec is not None:
        importlib.import_module("erp.models")
    else:
        LOGGER.debug("Model module not found during boot; skipping import")

    return app


__all__ = [
    "create_app",
    "register_blueprints",
    "db",
    "cache",
    "mail",
    "limiter",
    "login_manager",
    "redis_client",
    "socketio",
    "QUEUE_LAG",
    "RATE_LIMIT_REJECTIONS",
    "GRAPHQL_REJECTS",
    "AUDIT_CHAIN_BROKEN",
    "DLQ_MESSAGES",
    "_dead_letter_handler",
]
