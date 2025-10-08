# -*- coding: utf-8 -*-
"""
Main (public) routes.

This module only defines lightweight routes and exports `bp` so that
`erp.app:create_app()` (and Alembic's env.py which imports create_app)
can import it without side effects.
"""
from flask import Blueprint, render_template, url_for

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    # Keep a super-simple landing so it never 404s even if templates aren't ready.
    choose_url = url_for("main.choose_login")
    return f"<h1>ERP Backend</h1><p><a href='{choose_url}'>Choose role to log in</a></p>"

@bp.get("/choose-login")
def choose_login():
    # Renders the role picker (template already in your project).
    # The template can loop over these if it wants.
    roles = ("admin", "employee", "client")
    return render_template("choose-login.html", roles=roles)

@bp.get("/healthz")
def healthz():
    # Useful for uptime checks
    return {"status": "ok"}, 200
