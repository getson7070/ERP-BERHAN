from __future__ import annotations
from flask import Blueprint, jsonify

def simple_health(name, prefix=None):
    url_prefix = f"/{name}" if not prefix else prefix
    bp = Blueprint(name, __name__, url_prefix=url_prefix)
    @bp.get("/health")
    def health(): return jsonify({"status":"ok"})
    return bp


