# erp/routes/main.py
from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, abort
from jinja2 import TemplateNotFound

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    # Always send the visitor to the full UI chooser
    return redirect(url_for("main.choose_login"))

@bp.get("/healthz")
def healthz():
    return {"status": "ok"}, 200

# Support both spellings in the URL
@bp.get("/choose-login")
@bp.get("/choose_login")
def choose_login():
    # What the UI needs to render the three options
    roles = [
        {"key": "admin", "label": "Admin"},
        {"key": "employee", "label": "Employee"},
        {"key": "client", "label": "Client"},
    ]

    # Try common template names/locations (underscore, hyphen, in /auth or at root)
    candidates = [
        "choose_login.html",
        "choose-login.html",
        "auth/choose_login.html",
        "auth/choose-login.html",
    ]

    for name in candidates:
        try:
            return render_template(name, roles=roles)
        except TemplateNotFound:
            continue  # try the next candidate

    # If we get here, none of the files existed
    abort(
        500,
        description=(
            "Template for the chooser page was not found. "
            "Add one of these files in erp/templates/: "
            "choose_login.html or choose-login.html "
            "(optionally under erp/templates/auth/)."
        ),
    )
