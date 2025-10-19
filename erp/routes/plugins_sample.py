from __future__ import annotations
from flask import Blueprint, Response
bp = Blueprint("plugins_sample", __name__, url_prefix="/plugins/sample")
@bp.get("/")
def index():
    return Response("ok", mimetype="text/plain")


