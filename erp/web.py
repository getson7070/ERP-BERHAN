# erp/web.py
from __future__ import annotations
import os
from flask import Blueprint, render_template, redirect, url_for, current_app

bp = Blueprint("web", __name__)
web_bp = bp  # export alias

@bp.route("/")
def index():
    # If you want the home to be the chooser or a specific page, honor ENTRY_TEMPLATE env var.
    entry = os.getenv("ENTRY_TEMPLATE", "").strip()
    if entry:
        candidates = [
            entry,
            f"auth/{entry}",
            f"{entry.lstrip('/')}",
        ]
        for c in candidates:
            try:
                return render_template(c)
            except Exception:
                pass
    # fallback
    return redirect(url_for("web.choose_login"))

@bp.route("/choose_login")
def choose_login():
    return render_template("choose_login.html")

@bp.route("/health")
def health():
    return {"status": "ok"}
