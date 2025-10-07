# erp/routes/main.py
from flask import Blueprint, render_template

bp = Blueprint("main", __name__)

@bp.get("/choose_login")
def choose_login():
    return render_template("choose_login.html")
