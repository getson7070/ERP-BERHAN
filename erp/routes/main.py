# erp/routes/main.py
from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint("main", __name__)

@main_bp.get("/")
def index():
    return redirect(url_for("main.choose_login"))

@main_bp.get("/choose_login")
def choose_login():
    return render_template("choose_login.html")

# ---- Utility content pages to avoid 404s ----
@main_bp.get("/help")
def help_page():
    return render_template("misc/help.html")

@main_bp.get("/privacy")
def privacy_page():
    return render_template("misc/privacy.html")

@main_bp.get("/feedback")
def feedback_page():
    return render_template("misc/feedback.html")
