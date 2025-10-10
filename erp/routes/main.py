# erp/routes/main.py
from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("choose_login.html")

@main.route("/choose_login")
def choose_login():
    return render_template("choose_login.html")

@main.route("/help")
def help_page():
    return render_template("info/help.html")

@main.route("/privacy")
def privacy_page():
    return render_template("info/privacy.html")

@main.route("/feedback")
def feedback_page():
    return render_template("info/feedback.html")

@main.route("/health")
def health():
    return {"status": "ok"}, 200
