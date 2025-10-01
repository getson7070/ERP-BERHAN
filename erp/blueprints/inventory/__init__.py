# erp/blueprints/inventory/__init__.py
from __future__ import annotations

from flask import Blueprint, jsonify, request, abort

# ⛔️ DO NOT import anything from flask_jwt_extended at module top.
# ✅ Use our safe helpers that import only inside the request:
from erp.utils.jwt_helpers import require_jwt, get_jwt_claims, has_any_role

bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@bp.get("/items")
@require_jwt()  # replaces @jwt_required()
def list_items():
    """
    Example endpoint that previously used:
        @jwt_required()
        claims = get_jwt()
    """
    claims = get_jwt_claims()

    # OPTIONAL: enforce roles with our helper (adjust role names as needed).
    # If you used flask_security roles decorators before, this approximates that.
    if not has_any_role("inventory_view", "admin"):
        abort(403, description="Insufficient role")

    # Your real data access here — placeholder response to keep behavior stable.
    q = request.args.get("q", "")
    page = int(request.args.get("page", "1"))
    per_page = min(int(request.args.get("per_page", "50")), 200)

    # TODO: replace with actual DB query using SQLAlchemy models.
    return jsonify({
        "items": [],
        "query": q,
        "page": page,
        "per_page": per_page,
        "user": {
            "sub": claims.get("sub"),
            "roles": claims.get("roles", []),
        },
    })


@bp.get("/me")
@require_jwt()  # replaces @jwt_required()
def my_inventory_profile():
    """
    Another example that used get_jwt() at top level earlier.
    """
    claims = get_jwt_claims()
    profile = {
        "subject": claims.get("sub"),
        "email": claims.get("email"),
        "roles": claims.get("roles", []),
    }
    return jsonify(profile)
