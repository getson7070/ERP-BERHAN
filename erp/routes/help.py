"""Module: routes/help.py — audit-added docstring. Refine with precise purpose when convenient."""
from __future__ import annotations
from flask import Blueprint, render_template, Response

bp = Blueprint("help", __name__)
@bp.get("/help")
def help():
    """Serve the Help Center page with support guidance."""
    return render_template(
        "help.html",
        page_title="Help Center",
    )
@bp.get("/offline")
def offline():
    """Serve a simple HTML notice indicating the application is offline.

    This endpoint accepts no parameters and returns a minimal HTML response
    with a text message informing users that the application is currently
    unavailable.
    """
    return Response("<html><body>The application is offline.</body></html>", mimetype="text/html")



