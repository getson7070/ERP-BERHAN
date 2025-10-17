from .routes import bp

from flask import Blueprint, jsonify, abort
from flask_login import login_required
from erp.extensions import db
from .models import JournalEntry
from erp.approvals.rules import require_status, approve_doc, reverse_doc

finance_approval_bp = Blueprint("finance_approval", __name__, url_prefix="/finance")

@finance_approval_bp.post("/journals/<uuid:entry_id>/approve")
@login_required
def approve_journal(entry_id):
    je = db.session.get(JournalEntry, entry_id)
    if not je:
        abort(404, "Journal not found")
    require_status(je, {"Draft","Submitted"})
    approve_doc(je)
    db.session.commit()
    return jsonify({"id": str(je.id), "status": je.status})

@finance_approval_bp.post("/journals/<uuid:entry_id>/reverse")
@login_required
def reverse_journal(entry_id):
    je = db.session.get(JournalEntry, entry_id)
    if not je:
        abort(404, "Journal not found")
    require_status(je, {"Approved"})
    reverse_doc(je)
    # TODO: add mirror lines posting if your GL needs reversal entries
    db.session.commit()
    return jsonify({"id": str(je.id), "status": je.status})

