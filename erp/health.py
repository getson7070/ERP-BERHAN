"""Fallback health blueprint that mirrors the registry-backed contract."""

from __future__ import annotations

from http import HTTPStatus
import os
import time

from flask import Blueprint, jsonify
from sqlalchemy import text

from .extensions import db
from .health import health_registry

bp = Blueprint("health", __name__)


def _legacy_checks() -> tuple[bool, dict[str, dict[str, object]]]:
    """Run lightweight DB/Redis checks when the registry is unavailable."""

    results: dict[str, dict[str, object]] = {}
    overall_ok = True

    start = time.time()
    ok_db = True
    error_db: str | None = None
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - defensive guard
        ok_db = False
        error_db = str(exc)
        overall_ok = False
    duration_db = int((time.time() - start) * 1000)
    results["db"] = {
        "ok": ok_db,
        "critical": True,
        "duration_ms": duration_db,
        "detail": {},
        "error": error_db,
    }

    ru = os.getenv("REDIS_URL")
    start = time.time()
    ok_redis = True
    error_redis: str | None = None
    if ru:
        try:
            import redis

            redis.Redis.from_url(ru).ping()
        except Exception as exc:  # pragma: no cover - defensive guard
            ok_redis = False
            error_redis = str(exc)
            overall_ok = False

    duration_redis = int((time.time() - start) * 1000)
    results["redis"] = {
        "ok": ok_redis,
        "critical": False,
        "duration_ms": duration_redis,
        "detail": {},
        "error": error_redis,
    }

    return overall_ok, results


@bp.get("/healthz")
def healthz():
    try:
        ok, results = health_registry.run_all()
    except Exception:  # pragma: no cover - defensive guard
        ok, results = _legacy_checks()

    status_code = HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE
    return jsonify({"status": "ok" if ok else "error", "ok": ok, "checks": results}), status_code
