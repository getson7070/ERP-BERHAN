from __future__ import annotations
from flask import Blueprint, request, jsonify

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

def fetch_kpis():
    # tiny stub used by tests for monkeypatch
    return {"pending_orders": 0, "pending_maintenance": 0, "expired_tenders": 0, "monthly_sales": []}

def kpi_staleness_seconds() -> float:
    return 0.0

@bp.post("/vitals")
def vitals():
    data = request.get_json(silent=True) or {}
    # require a minimal shape
    if "event" not in data:
        return jsonify({"error": "invalid_schema"}), 400
    return jsonify({"status": "ok"})
