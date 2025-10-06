from flask import Blueprint, render_template, redirect, url_for
import os

web_bp = Blueprint("web", __name__)

@web_bp.get("/")
def root():
    return redirect(url_for("web.login_page"))

@web_bp.get("/choose_login")
def login_page():
    entry = os.getenv("ENTRY_TEMPLATE", "choose_login.html")
    return render_template(entry)

@web_bp.get("/login")
def login_alias():
    return redirect(url_for("auth.login"))

@web_bp.get("/employee_login")
def employee_login_alias():
    return redirect(url_for("auth.login"))
