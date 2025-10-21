# erp/inventory/routes.py â€” API for inventory + WAC shim
from __future__ import annotations
from decimal import Decimal
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from .models import Item, Warehouse, Lot, StockLedgerEntry
from ..extensions import db
from flask_login import login_required

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

@inventory_bp.route("/items", methods=["GET","POST"])
@login_required
def items():
    if request.method == "POST":
        data = request.get_json() or {}
        it = Item(sku=data["sku"], name=data["name"], uom=data.get("uom","Unit"))
        db.session.add(it); db.session.commit()
        return jsonify({"id": str(it.id)}), 201
    rows = Item.query.order_by(Item.sku).all()
    return jsonify([{"id":str(r.id),"sku":r.sku,"name":r.name,"uom":r.uom} for r in rows])

@inventory_bp.route("/warehouses", methods=["GET","POST"])
@login_required
def warehouses():
    if request.method == "POST":
        data = request.get_json() or {}
        w = Warehouse(name=data["name"])
        db.session.add(w); db.session.commit()
        return jsonify({"id": str(w.id)}), 201
    rows = Warehouse.query.order_by(Warehouse.name).all()
    return jsonify([{"id":str(r.id),"name":r.name} for r in rows])

def _onhand(item_id, warehouse_id=None):
    q = db.session.query(func.coalesce(func.sum(StockLedgerEntry.qty), 0))
    q = q.filter(StockLedgerEntry.item_id == item_id)
    if warehouse_id:
        q = q.filter(StockLedgerEntry.warehouse_id == warehouse_id)
    return Decimal(q.scalar() or 0)

@inventory_bp.route("/grn", methods=["POST"])
@login_required
def grn():
    data = request.get_json() or {}
    for ln in data.get("lines", []):
        sle = StockLedgerEntry(
            item_id=ln["item_id"],
            warehouse_id=ln["warehouse_id"],
            lot_id=ln.get("lot_id"),
            qty=Decimal(str(ln["qty"])),
            rate=Decimal(str(ln.get("rate", 0))),
            value=Decimal(str(ln.get("rate", 0))) * Decimal(str(ln["qty"])),
            voucher_type="GRN"
        )
        db.session.add(sle)
    db.session.commit()
    return jsonify({"status":"ok"}), 201

@inventory_bp.route("/delivery", methods=["POST"])
@login_required
def delivery():
    data = request.get_json() or {}
    for ln in data.get("lines", []):
        sle = StockLedgerEntry(
            item_id=ln["item_id"],
            warehouse_id=ln["warehouse_id"],
            lot_id=ln.get("lot_id"),
            qty=-abs(Decimal(str(ln["qty"]))),
            rate=Decimal(str(ln.get("rate", 0))),
            value=-abs(Decimal(str(ln.get("rate", 0))) * Decimal(str(ln["qty"]))),
            voucher_type="Delivery"
        )
        db.session.add(sle)
    db.session.commit()
    return jsonify({"status":"ok"}), 201


