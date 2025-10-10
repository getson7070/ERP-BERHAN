# erp/routes/auth.py
from flask import Blueprint, request, render_template

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    role = request.args.get("role", "client")
    # Template expected at erp/templates/auth/login.html
    return render_template("auth/login.html", role=role)
