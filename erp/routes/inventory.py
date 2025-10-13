# erp/routes/inventory.py — UI list that matches template
from flask import Blueprint, render_template, request
from sqlalchemy import func
from ..extensions import db
from ..inventory.models import Item, StockLedgerEntry

bp = Blueprint("inventory_ui", __name__, url_prefix="/inventory")

@bp.route("/")
def index():
    sku = request.args.get("sku")
    q = db.session.query(Item.id, Item.sku, Item.name, func.coalesce(func.sum(StockLedgerEntry.qty), 0).label("quantity"))            .outerjoin(StockLedgerEntry, StockLedgerEntry.item_id == Item.id)            .group_by(Item.id)
    if sku:
        q = q.filter(Item.sku == sku)
    items = [{"id": str(r.id), "sku": r.sku, "name": r.name, "quantity": float(r.quantity or 0)} for r in q.all()]
    return render_template("inventory/index.html", items=items)
