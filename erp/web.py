# erp/web.py
from flask import Blueprint, render_template, redirect, url_for

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    # send everyone to the login chooser
    return redirect(url_for("web.login_page"))

@web_bp.route("/choose_login")
def login_page():
    return render_template("choose_login.html")
