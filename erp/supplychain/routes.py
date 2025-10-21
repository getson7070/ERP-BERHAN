
from flask import Blueprint, request, jsonify
from flask_login import login_required
from erp.extensions import db
from .models import ReorderPolicy

supply_bp = Blueprint("supplychain", __name__, url_prefix="/supply")

@supply_bp.route("/policy", methods=["GET","POST"])
@login_required
def policy():
    if request.method == "POST":
        data = request.get_json() or {}
        obj = ReorderPolicy(item_id=data["item_id"], warehouse_id=data["warehouse_id"],
                            service_level=data.get("service_level",0.95),
                            safety_stock=data.get("safety_stock",0),
                            reorder_point=data.get("reorder_point",0))
        db.session.add(obj); db.session.commit()
        return jsonify({"id": str(obj.id)}), 201
    rows = ReorderPolicy.query.all()
    return jsonify([{"id": str(r.id), "item_id": str(r.item_id), "warehouse_id": str(r.warehouse_id),
                     "service_level": float(r.service_level or 0), "safety_stock": float(r.safety_stock or 0),
                     "reorder_point": float(r.reorder_point or 0)} for r in rows])


