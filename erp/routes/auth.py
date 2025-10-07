# erp/routes/auth.py
from flask import Blueprint, render_template, request

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET"])
def login():
    role = request.args.get("role", "client")
    return render_template("auth/login.html", role=role, title=f"{role.title()} Login")
