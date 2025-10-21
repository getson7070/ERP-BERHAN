
from datetime import datetime
from flask import abort
from flask_login import current_user

def require_status(doc, allowed: set[str]):
    if getattr(doc, "status", "Draft") not in allowed:
        abort(409, f"Invalid status: {getattr(doc, 'status', None)}; allowed: {allowed}")

def approve_doc(doc):
    if getattr(doc, "status", "Draft") == "Approved":
        return doc
    doc.status = "Approved"
    if hasattr(doc, "approved_at"):
        doc.approved_at = datetime.utcnow()
    if hasattr(doc, "approved_by") and getattr(current_user, 'id', None):
        doc.approved_by = getattr(current_user, 'id')
    return doc

def reverse_doc(doc, reversal_of=None):
    doc.status = "Reversed"
    if hasattr(doc, "reversed_at"):
        doc.reversed_at = datetime.utcnow()
    if hasattr(doc, "reversed_by") and getattr(current_user, 'id', None):
        doc.reversed_by = getattr(current_user, 'id')
    if hasattr(doc, "reversed_of") and reversal_of:
        doc.reversed_of = reversal_of
    return doc


