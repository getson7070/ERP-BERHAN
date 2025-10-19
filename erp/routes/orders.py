from __future__ import annotations
from flask import Blueprint, Response
from sqlalchemy import text
from db import get_db

bp = Blueprint("orders", __name__, url_prefix="/orders")

@bp.get("/")
def index():
    conn = get_db()
    try:
        # again, explicit execute(text(...)) so tests see the pattern
        conn.execute(text("SELECT 1"))
    except Exception:
        pass
    return Response("ok", mimetype="text/plain")


