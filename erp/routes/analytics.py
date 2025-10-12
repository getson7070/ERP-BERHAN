from flask import Blueprint, jsonify

# Keep this module harmless and independently importable.
# Do NOT import non-existent symbols from erp.observability.
analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@analytics_bp.get("/ping")
def ping():
    return jsonify(status="ok", module="analytics"), 200
