# erp/blueprints/login_ui.py
from flask import Blueprint, render_template
bp = Blueprint("login_ui", __name__)

@bp.get("/login")
def login():
    return render_template("login.html")
