# erp/routes/analytics.py
from flask import Blueprint, jsonify, render_template_string

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

try:
    from erp.observability import KPI_SALES_MV_AGE
except Exception:
    KPI_SALES_MV_AGE = "kpi:sales:mv_age"

@analytics_bp.get("/")
def analytics_home():
    return render_template_string("<h1 class='h4'>Analytics</h1><p>Coming soon.</p>")

@analytics_bp.get("/kpis")
def analytics_kpis():
    return jsonify({"KPI_SALES_MV_AGE": KPI_SALES_MV_AGE})
