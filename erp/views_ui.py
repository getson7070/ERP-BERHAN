from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint("ui", __name__)

@bp.route("/")
def root():
    return render_template("landing.html")

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)
