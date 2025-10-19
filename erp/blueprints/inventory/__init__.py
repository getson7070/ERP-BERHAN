from __future__ import annotations
from flask import Blueprint, session

bp = Blueprint("inventory_bp", __name__, url_prefix="/inventory")

def get_jwt():
    # tests monkeypatch this to inject {"org_id": 1}
    return {"org_id": session.get("org_id")}
