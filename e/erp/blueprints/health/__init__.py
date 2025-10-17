from flask import Blueprint, jsonify
import os
from erp.health_checks import check_database, check_redis, version_info

bp = Blueprint("health", __name__)

@bp.get("/healthz")
def healthz():
    # Liveness: process is up and can handle basic requests
    return jsonify({"status": "ok", **version_info()}), 200

@bp.get("/readyz")
def readyz():
    # Readiness: dependencies are ready (DB + Redis)
    checks = {
        "database": check_database(),
        "redis": check_redis(),
    }
    ready = all(x["ok"] for x in checks.values())
    code = 200 if ready else 503
    return jsonify({"ready": ready, "checks": checks, **version_info()}), code
