# erp/routes/main.py
from flask import Blueprint, render_template, redirect, url_for

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    # Only "client" login is public; show the chooser page with guarded tiles.
    return render_template("choose_login.html")

@bp.route("/choose_login")
def choose_login():
    return render_template("choose_login.html")

@bp.route("/help")
def help_page():
    return render_template("static_pages/help.html")

@bp.route("/privacy")
def privacy_page():
    return render_template("static_pages/privacy.html")

@bp.route("/feedback")
def feedback_page():
    return render_template("static_pages/feedback.html")
