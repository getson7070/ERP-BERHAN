from flask import Blueprint, jsonify, request
from erp.extensions import db
from erp.models.recall import ProductRecall

recall_bp = Blueprint("recall", __name__, url_prefix="/recall")

@recall_bp.get("/health")
def health():
    return jsonify(ok=True, module="recall")

@recall_bp.get("/items")
def list_recalls():
    rows = ProductRecall.query.order_by(ProductRecall.created_at.desc()).limit(50).all()
    return jsonify([{
        "id": r.id, "ref": r.ref, "product_name": r.product_name,
        "lot": r.lot, "reason": r.reason, "risk_level": r.risk_level,
        "status": r.status, "created_at": r.created_at.isoformat(), "closed_at": r.closed_at.isoformat() if r.closed_at else None
    } for r in rows])

@recall_bp.post("/items")
def create_recall():
    data = request.get_json() or {}
    missing = [k for k in ["ref","product_name","reason"] if not data.get(k)]
    if missing:
        return jsonify(error="missing_fields", fields=missing), 400
    r = ProductRecall(
        ref=data["ref"],
        product_name=data["product_name"],
        lot=data.get("lot"),
        reason=data["reason"],
        risk_level=data.get("risk_level","medium"),
        status=data.get("status","open"),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify(id=r.id, ref=r.ref), 201

# alias for dynamic importer
bp = recall_bp

