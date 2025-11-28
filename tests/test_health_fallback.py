"""Regression tests for the fallback `/healthz` handler."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from flask import Flask

from erp.health import health_registry
from erp.routes.health import bp as primary_health_bp


def _load_fallback_bp():
    module_path = Path(__file__).resolve().parents[1] / "erp" / "health.py"
    spec = importlib.util.spec_from_file_location("erp.health_fallback", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader  # for mypy
    spec.loader.exec_module(module)
    return module.bp, module


def test_fallback_healthz_matches_primary(monkeypatch):
    failing_results = {
        "db": {
            "ok": False,
            "critical": True,
            "duration_ms": 1,
            "detail": {},
            "error": "db down",
        }
    }

    monkeypatch.setattr(health_registry, "run_all", lambda: (False, failing_results))

    primary_app = Flask(__name__)
    primary_app.register_blueprint(primary_health_bp)
    primary_client = primary_app.test_client()

    fallback_bp, _fallback_module = _load_fallback_bp()
    fallback_app = Flask(__name__)
    fallback_app.register_blueprint(fallback_bp)
    fallback_client = fallback_app.test_client()

    primary_response = primary_client.get("/healthz")
    fallback_response = fallback_client.get("/healthz")

    assert primary_response.status_code == fallback_response.status_code == 503
    assert primary_response.get_json() == fallback_response.get_json()
    assert fallback_response.get_json()["status"] == "error"
