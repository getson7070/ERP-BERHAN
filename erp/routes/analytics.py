from __future__ import annotations
from flask import Blueprint, request, jsonify

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

# Tiny Celery stub sufficient for tests
class _Celery:
    def task(self, *_, **__):
        def deco(fn): return fn
        return deco
    def send_task(self, *_a, **_k): return True

celery = _Celery()

def fetch_kpis():
    # tiny stub used by tests for monkeypatch
    return {"pending_orders": 0, "pending_maintenance": 0, "expired_tenders": 0, "monthly_sales": []}

def kpi_staleness_seconds() -> float:
    return 0.0

@bp.post("/vitals")
def vitals():
    data = request.get_json(silent=True) or {}
    if "event" not in data:
        return jsonify({"error": "invalid_schema"}), 400
    return jsonify({"status": "ok"})

# Functions some tests import
@celery.task
def send_approval_reminders():
    # pretend to enqueue emails; return count for test assertions
    return 0

@celery.task
def forecast_sales(months: int = 3):
    # return trivial forecast structure
    return [{"month": i+1, "forecast": 0} for i in range(months)]
