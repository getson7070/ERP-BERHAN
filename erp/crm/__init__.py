# -*- coding: utf-8 -*-
from __future__ import annotations
from flask import Blueprint, jsonify

bp = Blueprint("crm", __name__, url_prefix="/crm")

@bp.get("/")
def home():
    return jsonify(module="crm", ok=True)

# If you later add crm.security, it should define its OWN bp (e.g., bp_security)
# and you can import/register it explicitly from app factory or here guardedly:
# try:
#     from .security import bp as bp_security  # noqa: F401
# except Exception:
#     bp_security = None