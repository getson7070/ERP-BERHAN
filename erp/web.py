# erp/web.py
from flask import Blueprint, jsonify, redirect, url_for

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    # Always land on the real login view implemented in erp.routes.auth
    return redirect(url_for("auth.login"))

@web_bp.route("/auth/login")
def login_page():
    # If someone hits this via old links, send to the real auth view
    return redirect(url_for("auth.login"))

@web_bp.route("/health")
def health():
    return jsonify({"status": "ok"}), 200
