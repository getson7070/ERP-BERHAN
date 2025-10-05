# erp/web.py
from __future__ import annotations

import os
from flask import Blueprint, jsonify, redirect, render_template, url_for
from werkzeug.routing import BuildError
from pathlib import Path

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    # Try to go to login; if auth isn't registered yet, show fallback page
    try:
        return redirect(url_for("auth.login"))
    except BuildError:
        return redirect(url_for("web.choose_login"))

@web_bp.route("/choose_login")
def choose_login():
    # Fallback helper page, shows up if auth blueprint isn't registered yet
    candidates = [
        "auth/login.html",
        "choose_login.html",
        "login.html",
        "index.html",
    ]
    root = Path(web_bp.root_path).parent.parent / "templates"
    existing = [t for t in candidates if (root / t).exists()]
    if existing:
        # prefer ENTRY_TEMPLATE if the file actually exists
        entry = os.getenv("ENTRY_TEMPLATE")
        if entry and (root / entry).exists():
            return render_template(entry)
        return render_template(existing[0])

    # Minimal text page if no template exists (matches the page you saw)
    msg = "ERP-BERHAN is running.\nExpected one of: " + ", ".join(f"templates/{t}" for t in candidates)
    msg += "\n\nHealth: /health"
    return msg, 200, {"Content-Type": "text/plain; charset=utf-8"}

@web_bp.route("/health")
def health():
    return jsonify({"status": "ok"})
