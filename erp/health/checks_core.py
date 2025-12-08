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

    ok = bool(current_version and current_version in heads)
    return {"ok": ok, "current": current_version, "heads": sorted(heads)}


def _register_checks() -> None:
    try:
        health_registry.register(HealthCheck("db", db_check, critical=True))
        health_registry.register(HealthCheck("db_migrations", db_migrations, critical=True))
        health_registry.register(HealthCheck("redis", redis_check, critical=False))
        health_registry.register(HealthCheck("telegram_cfg", telegram_configured, critical=False))
        health_registry.register(HealthCheck("banking", banking_service, critical=False))
    except Exception:  # pragma: no cover - registry may be unavailable in lightweight runs
        return


_register_checks()
