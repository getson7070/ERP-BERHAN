from flask import Blueprint, jsonify
from .models import PurchaseOrder  # noqa: F401

bp = Blueprint("procurment", __name__)


@bp.get("/procurment/health")
def health():
    return jsonify({"ok": True})


