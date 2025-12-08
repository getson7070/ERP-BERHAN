"""Help Center routes providing support access and offline notice."""
from __future__ import annotations
import os
from flask import Blueprint, render_template, Response, current_app

bp = Blueprint("help", __name__)
def _support_context(cfg):
    env_email = os.getenv("SUPPORT_EMAIL")
    env_phone = os.getenv("SUPPORT_PHONE")
    env_hours = os.getenv("SUPPORT_HOURS")
    env_sla = os.getenv("SUPPORT_RESPONSE_SLA")
    return {
        "page_title": "Help Center",
        "support_email": env_email or cfg.get("SUPPORT_EMAIL") or "support@example.com",
        "support_phone": env_phone or cfg.get("SUPPORT_PHONE") or "",
        "support_hours": env_hours or cfg.get("SUPPORT_HOURS") or "",
        "support_response_sla": env_sla or cfg.get("SUPPORT_RESPONSE_SLA") or "",
        "system_status": cfg.get("HELP_SYSTEM_STATUS", ()) or (),
    }


@bp.get("/help")
def help():
    """Serve the Help Center page with support guidance and live config values."""
    return render_template("help.html", **_support_context(current_app.config))
@bp.get("/offline")
def offline():
    """Serve a simple HTML notice indicating the application is offline.

    This endpoint accepts no parameters and returns a minimal HTML response
    with a text message informing users that the application is currently
    unavailable.
    """
    return Response("<html><body>The application is offline.</body></html>", mimetype="text/html")



