from __future__ import annotations
from flask import Blueprint, request, jsonify

bp = Blueprint("analytics", __name__)

@bp.get("/dashboard")
def dashboard():
    return jsonify({"ok": True})

@bp.post("/vitals")
def vitals():
    data = request.get_json(silent=True) or {}
    # Require at least one expected field; tests post bad payload and expect 400
    if "latency_ms" not in data and "cpu" not in data and "mem" not in data:
        return jsonify({"error": "bad schema"}), 400
    return jsonify({"ok": True})
