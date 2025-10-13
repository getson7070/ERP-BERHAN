from flask import Blueprint, request, jsonify
from flask_login import login_required
from decimal import Decimal

try:
    # Prefer your project modules if present
    from erp.inventory.models import Delivery, StockLedgerEntry
    from erp.inventory.valuation import post_sle
    from erp.extensions import db
except Exception:
    # Fallback shims for older layouts
    from extensions import db  # type: ignore
    Delivery = None
    StockLedgerEntry = None
    def post_sle(item_id, warehouse_id, qty, voucher_type, voucher_id, lot_id=None, rate=None):
        raise RuntimeError("post_sle not available; add erp.inventory.valuation.post_sle")

inventory_delivery_bp = Blueprint("inventory_delivery", __name__, url_prefix="/inventory")

@inventory_delivery_bp.route("/delivery", methods=["POST"])
@login_required
def create_delivery():
    data = request.get_json(silent=True) or {}
    # allow running without Delivery model
    delivery_id = None
    if Delivery is not None:
        d = Delivery(customer_id=data.get("customer_id"))
        db.session.add(d); db.session.flush()
        delivery_id = d.id
    for ln in data.get("lines", []):
        qty = Decimal(str(ln.get("qty", 0)))
        if qty > 0:
            qty = -qty  # issues are negative
        post_sle(item_id=ln["item_id"],
                 warehouse_id=ln["warehouse_id"],
                 qty=qty,
                 voucher_type="Delivery",
                 voucher_id=delivery_id,
                 lot_id=ln.get("lot_id"))
    db.session.commit()
    return jsonify(dict(id=str(delivery_id) if delivery_id else None)), 201
