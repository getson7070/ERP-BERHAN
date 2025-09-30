from flask import Blueprint, render_template
from erp.utils import login_required

bp = Blueprint("main", __name__)

@bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
