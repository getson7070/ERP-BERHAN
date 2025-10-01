from flask import Blueprint, render_template, redirect, url_for
from erp.extensions import limiter

bp = Blueprint("auth", __name__)

# Show the login page (no redirect loops, actually render the template)
@bp.get("/login")
@limiter.limit("20/minute")
def login():
    # Template exists at templates/auth/login.html in your repo
    return render_template("auth/login.html")

# Backward-compat route some code referenced earlier (auth.choose_login)
@bp.get("/choose-login")
def choose_login():
    # Just send users to the same login page
    return redirect(url_for("auth.login"))
