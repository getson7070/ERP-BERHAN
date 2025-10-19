from __future__ import annotations
from flask import Blueprint, jsonify
from erp.utils import idempotent

bp = Blueprint("misc", __name__)

@bp.post("/idem")
@idempotent
def idem():
    return jsonify({"status": "ok"})


