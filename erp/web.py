from __future__ import annotations
from flask import Blueprint, render_template, jsonify, redirect, url_for

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    return redirect(url_for("web.choose_login"))

@web_bp.route("/choose_login")
def choose_login():
    expected = [
        "templates/auth/login.html",
        "templates/choose_login.html",
        "templates/login.html",
        "templates/index.html",
    ]
    return render_template("choose_login.html", expected=expected)

@web_bp.route("/health")
def health():
    return jsonify({"status": "ok"})
