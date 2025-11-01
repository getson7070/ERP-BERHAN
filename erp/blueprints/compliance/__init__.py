"""API endpoints for compliance workflows."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_security import auth_required, roles_required

from ...extensions import db
from ...compliance import ElectronicSignature, BatchRecord

bp = Blueprint("compliance", __name__, url_prefix="/api/compliance")


@bp.post("/signatures")
@auth_required("token")
@roles_required("auditor")
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
@auth_required("token")
@roles_required("auditor")
def get_batch_record(record_id: int):
    record = BatchRecord.query.get_or_404(record_id)
    return jsonify(
        {
            "id": record.id,
            "lot_number": record.lot_number,
            "description": record.description,
        }
    )


