# erp/routes/main.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint("main", __name__)

@bp.get("/choose_login")
def choose_login():
    return render_template("choose_login.html")

@bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)
