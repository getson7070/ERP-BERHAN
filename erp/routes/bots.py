"""Bot integration endpoints (health / status).

This blueprint intentionally remains small. All operational endpoints must be
protected by policy-based permissions to avoid exposing internal signals.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from erp.security_decorators_phase2 import require_permission

bp = Blueprint("bots", __name__, url_prefix="/bots")


@bp.get("/slack/health")
@require_permission("bots", "health")
def slack_health():
    """Health endpoint for bot integrations."""
    return jsonify({"ok": True})
