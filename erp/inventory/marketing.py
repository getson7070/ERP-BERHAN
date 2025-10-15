from __future__ import annotations
from flask import Blueprint, render_template
from flask_login import login_required

marketing_bp = Blueprint("marketing", __name__, template_folder="../templates/marketing")

@marketing_bp.get("/")
@login_required
def index():
    # Placeholder dashboard (campaigns/leads KPIs can be added here)
    return render_template("marketing/index.html")
