"""API endpoints for compliance workflows."""

from __future__ import annotations

from functools import wraps

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from ...extensions import db
from ...compliance import ElectronicSignature, BatchRecord
from ...models import UserRoleAssignment, Role

bp = Blueprint("compliance", __name__, url_prefix="/api/compliance")


def _require_role(role_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            assignment = (
                UserRoleAssignment.query.join(Role, Role.id == UserRoleAssignment.role_id)
                .filter(UserRoleAssignment.user_id == current_user.id, Role.name == role_name)
                .first()
            )
            if assignment is None:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@bp.post("/signatures")
@login_required
@_require_role("auditor")
def create_signature():
    """Record an electronic signature."""
    data = request.get_json() or {}
    sig = ElectronicSignature(
        user_id=data.get("user_id"),
        intent=data.get("intent", ""),
    )
    db.session.add(sig)
    db.session.commit()
    return jsonify({"id": sig.id, "hash": sig.signature_hash})


@bp.get("/batch-records/<int:record_id>")
@login_required
@_require_role("auditor")
def get_batch_record(record_id: int):
    record = BatchRecord.query.get_or_404(record_id)
    return jsonify(
        {
            "id": record.id,
            "lot_number": record.lot_number,
            "description": record.description,
        }
    )


