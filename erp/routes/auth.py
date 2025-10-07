from __future__ import annotations
from flask import Blueprint, render_template, request

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login")
def login():
    role = request.args.get("role", "client")
    # templates/auth/login.html should exist
    return render_template("auth/login.html", role=role)

@auth_bp.route("/employee_login")
def employee_login():
    return render_template("auth/login.html", role="employee")

@auth_bp.route("/client_login")
def client_login():
    return render_template("auth/login.html", role="client")
