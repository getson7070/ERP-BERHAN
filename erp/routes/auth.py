# erp/routes/auth.py
from flask import Blueprint, redirect, url_for

auth_bp = Blueprint("auth", __name__)

@auth_bp.get("/login")
def login():
    # Until a dedicated auth/login.html is reinstated, reuse chooser
    return redirect(url_for("web.login_page"))

@auth_bp.get("/employee_login")
def employee_login():
    return redirect(url_for("web.login_page"))

@auth_bp.get("/client_login")
def client_login():
    return redirect(url_for("web.login_page"))
