from __future__ import annotations
from flask import Blueprint, render_template, Response

bp = Blueprint("help", __name__)
@bp.get("/help")
def help():
    try:
        return render_template("help.html")
    except Exception:
        return Response("<html><body><h1>Help</h1></body></html>", mimetype="text/html")
@bp.get("/offline")
def offline():
    return Response("<html><body>The application is offline</body></html>", mimetype="text/html")


