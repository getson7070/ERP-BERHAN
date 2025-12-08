"""Core health checks for database and key integrations."""
from __future__ import annotations

import os
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory

from flask import current_app
from sqlalchemy import inspect, text

from db import redis_client
from erp.extensions import db
from erp.health.registry import HealthCheck, health_registry
from erp.services.banking_client import banking_ping
from erp.utils import resolve_org_id


def db_check() -> dict[str, Any]:
    db.session.execute(text("SELECT 1"))
    return {"ok": True}


def redis_check() -> dict[str, Any]:
    try:
        redis_client.set("__health__", "1", ex=60)
        redis_client.delete("__health__")
        return {"ok": True}
    except Exception:
        return {"ok": False}


def telegram_configured() -> dict[str, Any]:
    bots_defined = bool(
        os.getenv("TELEGRAM_BOTS_JSON")
        or os.getenv("TELEGRAM_BOT_TOKEN")
        or os.getenv("TELEGRAM_DEFAULT_BOT")
    )
    return {"ok": bots_defined}


def banking_service() -> dict[str, Any]:
    org_id = None
    try:
        org_id = resolve_org_id()
    except Exception:
        org_id = None

    ok = banking_ping(org_id)
    return {"ok": ok}


def db_migrations() -> dict[str, Any]:
    """Validate that the running database is aligned with the latest Alembic head.

    In testing or when ALLOW_INSECURE_DEFAULTS=1 is set, the check is skipped
    unless MIGRATION_CHECK_STRICT=1 forces validation to run. This keeps local
    and CI setups lightweight while still surfacing drift in higher
    environments.
    """

    strict = os.getenv("MIGRATION_CHECK_STRICT", "0") == "1"
    allow_insecure = os.getenv("ALLOW_INSECURE_DEFAULTS") == "1"
    testing = False
    try:
        testing = bool(current_app.config.get("TESTING"))
    except Exception:
        testing = False

    if (testing or allow_insecure) and not strict:
        return {"ok": True, "skipped": True, "reason": "testing_or_insecure_mode"}

    with db.engine.connect() as connection:
        inspector = inspect(connection)
        if not inspector.has_table("alembic_version"):
            return {"ok": False, "current": None, "heads": None, "error": "missing_alembic_version_table"}

        current_version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar()

    try:
        alembic_ini = os.getenv("ALEMBIC_INI_PATH", "alembic.ini")
        cfg = Config(alembic_ini)
        script = ScriptDirectory.from_config(cfg)
        heads = set(script.get_heads())
    except Exception as exc:  # pragma: no cover - defensive guard for misconfigured paths
        return {
            "ok": False,
            "current": current_version,
            "heads": None,
            "error": f"head_discovery_failed: {exc}",
        }

    if len(heads) > 1:
        return {
            "ok": False,
            "current": current_version,
            "heads": sorted(heads),
            "error": "multiple_heads_detected",
            "resolution": "Apply merge revision 20251212100000 or manually merge the heads",
        }

    ok = bool(current_version and current_version in heads)
    return {"ok": ok, "current": current_version, "heads": sorted(heads)}


def config_sanity() -> dict[str, Any]:
    """Validate core deployment secrets and database configuration.

    The check defaults to a strict stance in production while allowing
    local/test environments to opt out unless CONFIG_CHECK_STRICT=1 forces
    validation. Weak defaults (e.g., "change-me" placeholders) or sqlite
    database URLs in production are treated as failures to reduce the risk
    of insecure rollouts.
    """

    allow_insecure = os.getenv("ALLOW_INSECURE_DEFAULTS") == "1"
    strict = os.getenv("CONFIG_CHECK_STRICT", "0") == "1"
    env_flag = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "").lower()
    production = env_flag == "production"

    testing = False
    try:
        testing = bool(current_app.config.get("TESTING"))
    except Exception:
        testing = False

    if (testing or allow_insecure) and not strict:
        return {"ok": True, "skipped": True, "reason": "testing_or_insecure_mode"}

    secret_key = os.getenv("SECRET_KEY")
    db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    jwt_secret = os.getenv("JWT_SECRET_KEY")

    missing = [
        key
        for key, value in (
            ("SECRET_KEY", secret_key),
            ("DATABASE_URL", db_url),
            ("JWT_SECRET_KEY", jwt_secret),
        )
        if not value
    ]

    weak_markers = {"change-me", "change-me-in-prod"}
    weak_defaults = []
    if secret_key in weak_markers:
        weak_defaults.append("SECRET_KEY")
    if jwt_secret in weak_markers:
        weak_defaults.append("JWT_SECRET_KEY")

    insecure_sqlite = bool(db_url and db_url.startswith("sqlite://") and (production or strict))

    ok = not missing and not weak_defaults and not insecure_sqlite
    return {
        "ok": ok,
        "missing": missing,
        "weak_defaults": weak_defaults,
        "insecure_sqlite": insecure_sqlite,
        "production": production or strict,
    }


def _register_checks() -> None:
    try:
        health_registry.register(HealthCheck("db", db_check, critical=True))
        health_registry.register(HealthCheck("config", config_sanity, critical=True))
        health_registry.register(HealthCheck("db_migrations", db_migrations, critical=True))
        health_registry.register(HealthCheck("redis", redis_check, critical=False))
        health_registry.register(HealthCheck("telegram_cfg", telegram_configured, critical=False))
        health_registry.register(HealthCheck("banking", banking_service, critical=False))
    except Exception:  # pragma: no cover - registry may be unavailable in lightweight runs
        return


_register_checks()
