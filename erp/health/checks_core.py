"""Core health checks for database and key integrations."""
from __future__ import annotations

import os
from typing import Any

from sqlalchemy import text

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


def _register_checks() -> None:
    try:
        health_registry.register(HealthCheck("db", db_check, critical=True))
        health_registry.register(HealthCheck("redis", redis_check, critical=False))
        health_registry.register(HealthCheck("telegram_cfg", telegram_configured, critical=False))
        health_registry.register(HealthCheck("banking", banking_service, critical=False))
    except Exception:  # pragma: no cover - registry may be unavailable in lightweight runs
        return


_register_checks()
