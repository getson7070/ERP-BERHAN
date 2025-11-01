from flask import jsonify

def get_report():
    return jsonify({"report": "Analytics data here"})
from flask import jsonify

def get_report():
    # Pharma analytics with batch tracking
    return jsonify({"batch_status": "Compliant", "sales": 1000, "trace_id": "GMP-123"})
from flask import jsonify
from erp.models import db

def get_report():
    # Pharma GMP report with traceability
    data = db.session.query(Ledger).all()
    return jsonify([{"id": d.id, "trace_id": d.trace_id} for d in data])
