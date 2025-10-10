# erp/routes/main.py
from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # land on the chooser
    return render_template("choose_login.html")

@main_bp.route("/choose_login")
def choose_login():
    return render_template("choose_login.html")

@main_bp.route("/help")
def help_page():
    return render_template("help.html")

@main_bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")

@main_bp.route("/feedback")
def feedback_page():
    return render_template("feedback.html")

@main_bp.route("/health")
def health():
    return ("OK", 200)
