# erp/blueprints/health/__init__.py
from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.get("/health/live")
def liveness():
    # Process is up; add-only checks.
    return jsonify(status="ok"), 200

@bp.get("/health/ready")
def readiness():
    # Be generous in dev/test; deeper checks can be added later.
    return jsonify(status="ready"), 200
