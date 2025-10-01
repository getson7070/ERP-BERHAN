from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@bp.get("/health")
def inventory_health():
    # Import inside the request to avoid module-level LocalProxy creation
    try:
        from flask_jwt_extended import current_user  # local import on purpose

        user_repr = repr(current_user)
    except Exception:
        user_repr = None

    return jsonify({"status": "ok", "current_user": user_repr})
