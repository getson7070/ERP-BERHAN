
from flask import Blueprint, jsonify, abort
from flask_login import login_required
from erp.extensions import db
from .models import GRN, Delivery
from erp.approvals.rules import require_status, approve_doc, reverse_doc

inventory_approval_bp = Blueprint("inventory_approval", __name__, url_prefix="/inventory")

@inventory_approval_bp.post("/grn/<uuid:doc_id>/approve")
@login_required
def approve_grn(doc_id):
    d = db.session.get(GRN, doc_id)
    if not d:
        abort(404, "GRN not found")
    require_status(d, {"Draft","Submitted"})
    approve_doc(d)
    db.session.commit()
    return jsonify({"id": str(d.id), "status": d.status})

@inventory_approval_bp.post("/grn/<uuid:doc_id>/reverse")
@login_required
def reverse_grn(doc_id):
    d = db.session.get(GRN, doc_id)
    if not d:
        abort(404, "GRN not found")
    require_status(d, {"Approved"})
    reverse_doc(d)
    db.session.commit()
    return jsonify({"id": str(d.id), "status": d.status})

@inventory_approval_bp.post("/delivery/<uuid:doc_id>/approve")
@login_required
def approve_delivery(doc_id):
    d = db.session.get(Delivery, doc_id)
    if not d:
        abort(404, "Delivery not found")
    require_status(d, {"Draft","Submitted"})
    approve_doc(d)
    db.session.commit()
    return jsonify({"id": str(d.id), "status": d.status})

@inventory_approval_bp.post("/delivery/<uuid:doc_id>/reverse")
@login_required
def reverse_delivery(doc_id):
    d = db.session.get(Delivery, doc_id)
    if not d:
        abort(404, "Delivery not found")
    require_status(d, {"Approved"})
    reverse_doc(d)
    db.session.commit()
    return jsonify({"id": str(d.id), "status": d.status})


