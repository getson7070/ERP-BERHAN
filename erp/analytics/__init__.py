from flask import Blueprint

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@bp.get("/health")
def health():
    return {"module": "analytics", "ok": True}