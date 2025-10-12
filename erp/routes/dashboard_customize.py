# erp/routes/dashboard_customize.py
from flask import Blueprint, render_template, abort
from erp.extensions import db
import erp.models as models

dashboard_customize_bp = Blueprint("dashboard_customize", __name__, url_prefix="/dashboard-customize")

@dashboard_customize_bp.get("/")
def customize():
    UserDashboard = getattr(models, "UserDashboard", None)
    if UserDashboard is None:
        abort(404)
    items = UserDashboard.query.limit(10).all()
    return render_template("dashboard/customize.html", items=items)
