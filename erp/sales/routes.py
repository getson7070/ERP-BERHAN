from flask import Blueprint, jsonify
from .models import SalesOrder  # noqa: F401

bp = Blueprint("sales", __name__)


@bp.get("/sales/health")
def health():
    return jsonify({"ok": True})


