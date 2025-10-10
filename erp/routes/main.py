from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return redirect(url_for("main.choose_login"))

@main_bp.route("/choose_login")
def choose_login():
    # Only client login is public; others appear disabled
    return render_template("choose_login.html")

@main_bp.route("/help")
def help_page():
    return render_template("info/help.html")

@main_bp.route("/privacy")
def privacy_page():
    return render_template("info/privacy.html")

@main_bp.route("/feedback")
def feedback_page():
    return render_template("info/feedback.html")
