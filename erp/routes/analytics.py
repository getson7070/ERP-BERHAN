# erp/routes/analytics.py
from flask import Blueprint, jsonify, current_app

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@analytics_bp.route("/kpis")
def kpis():
    """Return KPIs; tolerate missing observability symbols so analytics never breaks the app."""
    try:
        import erp.observability as obs
    except Exception as e:
        current_app.logger.warning("Observability import failed: %r", e)
        obs = None

    # Safely read counters/values if present; otherwise return zeros/defaults
    def _get(name, default):
        return getattr(obs, name, default) if obs else default

    payload = {
        "kpi_sales_mv_age": _get("KPI_SALES_MV_AGE", 0),
        "token_errors": _get("TOKEN_ERRORS", []),
        "graphql_rejects": _get("GRAPHQL_REJECTS", []),
    }
    return jsonify(payload)
