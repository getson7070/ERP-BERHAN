"""Health endpoints backed by the shared health registry."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify

import erp.health.checks_core  # noqa: F401 - registers baseline checks
from erp.health import health_registry

bp = Blueprint("health", __name__)


def _response_from_registry():
    ok, results = health_registry.run_all()
    return ok, results


@bp.get("/health")
def health():
    ok, results = _response_from_registry()
    status_code = HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE
    return jsonify({"ok": ok, "checks": results}), status_code


@bp.get("/healthz")
def healthz():
    ok, results = _response_from_registry()
    status_code = HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE
    return jsonify({"ok": ok, "checks": results}), status_code


@bp.get("/readyz")
def readyz():
    ok, results = _response_from_registry()
    critical_ok = all(v["ok"] for v in results.values() if v.get("critical"))
    status_code = HTTPStatus.OK if critical_ok else HTTPStatus.SERVICE_UNAVAILABLE
    return jsonify({"ok": critical_ok, "checks": results}), status_code

