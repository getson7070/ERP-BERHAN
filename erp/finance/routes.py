from flask import Blueprint, jsonify, request  # noqa: F401
from .models import Account, JournalEntry, JournalLine, Invoice, Bill  # noqa: F401

bp = Blueprint("finance", __name__)


@bp.get("/finance/health")
def health():
    return jsonify({"ok": True})
