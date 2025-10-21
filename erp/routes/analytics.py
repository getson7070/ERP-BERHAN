from flask import Blueprint, request, jsonify

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@bp.post("/vitals")
def collect_vitals():
    data = request.get_json(silent=True) or {}
    # minimal schema expected by tests: require cpu & mem
    if not {"cpu", "mem"}.issubset(data.keys()):
        return jsonify({"error": "bad schema"}), 400
    return jsonify({"ok": True})
