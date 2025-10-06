# erp/web.py
from flask import Blueprint, render_template, redirect, url_for

web_bp = Blueprint("web", __name__)

@web_bp.route("/choose_login")
def login_page():
    # ENTRY_TEMPLATE kept simple; choose_login.html exists in erp/templates
    return render_template("choose_login.html")

# Back-compat routes that used to exist
@web_bp.route("/login")
def compat_login():
    return redirect(url_for("web.login_page"))
