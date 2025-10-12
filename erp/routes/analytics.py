from __future__ import annotations

from flask import Blueprint, jsonify, current_app

# Blueprint (auto-registered by erp.__init__._register_blueprints)
bp = Blueprint("analytics", __name__, url_prefix="/analytics")

# Some deployments don't ship the optional observability module or parts of it.
# Import defensively so app startup never fails.
try:  # pragma: no cover - import guard
    from erp.observability import KPI_SALES_MV_AGE  # type: ignore
except Exception:  # noqa: BLE001
    KPI_SALES_MV_AGE = None  # Fallback: route will return "unavailable"


@bp.get("/health")
def analytics_health():
    return {"ok": True}, 200


@bp.get("/kpi/sales-mv-age")
def kpi_sales_mv_age():
    """
    Returns KPI_SALES_MV_AGE in a resilient way:
    - If it's a callable, call it.
    - If it's a constant/value, return it.
    - If it's missing, return a structured 'unavailable' payload.
    """
    if KPI_SALES_MV_AGE is None:
        return jsonify({"metric": "KPI_SALES_MV_AGE", "status": "unavailable"}), 200

    try:
        value = KPI_SALES_MV_AGE() if callable(KPI_SALES_MV_AGE) else KPI_SALES_MV_AGE
        return jsonify({"metric": "KPI_SALES_MV_AGE", "value": value}), 200
    except Exception as exc:  # noqa: BLE001
        current_app.logger.exception("Failed to compute KPI_SALES_MV_AGE: %s", exc)
        return jsonify({"metric": "KPI_SALES_MV_AGE", "status": "error"}), 500
