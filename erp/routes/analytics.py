# erp/routes/analytics.py
from flask import Blueprint, jsonify

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@analytics_bp.route("/health")
def health():
    return jsonify({"status": "ok"})
