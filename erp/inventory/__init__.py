from flask import Blueprint

bp = Blueprint("inventory", __name__, url_prefix="/inventory")

@bp.get("/")
def index():
    return {"module": "inventory", "ok": True}