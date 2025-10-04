# erp/web.py
from __future__ import annotations

import os
from typing import Optional

from flask import Blueprint, current_app, render_template, redirect, url_for

bp = Blueprint("web", __name__)

ENTRY_CANDIDATES = (
    "auth/login.html",
    "choose_login.html",
    "login.html",
    "index.html",
)

def _exists(name: str) -> bool:
    """Does a template exist in either search path?"""
    try:
        current_app.jinja_env.get_or_select_template(name)
        return True
    except Exception:
        return False

def _choose_entry() -> Optional[str]:
    """Choose the first viable entry template, honoring ENTRY_TEMPLATE env/config."""
    explicit = (
        current_app.config.get("ENTRY_TEMPLATE")
        or os.getenv("ENTRY_TEMPLATE")
        or ""
    ).strip()
    if explicit:
        return explicit if _exists(explicit) else None

    for cand in ENTRY_CANDIDATES:
        if _exists(cand):
            return cand
    return None

@bp.route("/health")
def health():
    return {"app": "ERP-BERHAN", "status": "running"}

@bp.route("/")
def index():
    # If auth blueprint is registered, prefer redirecting to it.
    if "auth.login" in current_app.view_functions:
        return redirect(url_for("auth.login"))

    chosen = _choose_entry()
    if chosen:
        return render_template(chosen)

    current_app.logger.warning(
        "No entry template found under templates/ or erp/templates/."
    )
    return render_template("fallback.html")
