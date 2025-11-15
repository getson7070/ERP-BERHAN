# -*- coding: utf-8 -*-
from __future__ import annotations
from flask import Blueprint, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.get("/health")
def health():
    return jsonify(ok=True, module="api")
