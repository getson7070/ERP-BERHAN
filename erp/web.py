# erp/web.py
from flask import Blueprint, render_template, jsonify

# Name it web_bp so app.py can import it
web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    # Render the configured entry template; fall back to choose_login.html
    # (Render will 500 if the template doesn't exist, so make sure it's there.)
    return render_template("choose_login.html")

@web_bp.route("/choose_login")
def choose_login():
    return render_template("choose_login.html")

@web_bp.route("/auth/login")
def auth_login():
    # Your template is templates/login.html (not auth/login.html)
    return render_template("login.html")

@web_bp.route("/health")
def health():
    return jsonify({"status": "ok"})
