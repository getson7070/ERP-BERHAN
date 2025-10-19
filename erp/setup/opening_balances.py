
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from datetime import date
from decimal import Decimal
from erp.extensions import db
from erp.finance.models import JournalEntry, JournalLine
from erp.inventory.valuation import post_sle

setup_bp = Blueprint("setup_opening", __name__, url_prefix="/setup")

@setup_bp.get("/opening/gl")
@login_required
def opening_gl_form():
    return render_template("setup/opening_gl.html")

@setup_bp.post("/opening/gl")
@login_required
def opening_gl_load():
    payload = request.get_json(silent=True) or {}
    posting_date = date.fromisoformat(payload.get("posting_date"))
    lines = payload.get("lines", [])
    if not lines:
        return jsonify({"error":"No lines"}), 400
    je = JournalEntry(posting_date=posting_date, reference="Opening Balance")
    db.session.add(je); db.session.flush()
    for ln in lines:
        db.session.add(JournalLine(
            entry_id=je.id,
            account_id=ln["account_id"],
            debit=ln.get("debit",0),
            credit=ln.get("credit",0),
            description=ln.get("description")
        ))
    db.session.commit()
    return jsonify({"journal_id": str(je.id)}), 201

@setup_bp.get("/opening/stock")
@login_required
def opening_stock_form():
    return render_template("setup/opening_stock.html")

@setup_bp.post("/opening/stock")
@login_required
def opening_stock_load():
    payload = request.get_json(silent=True) or {}
    items = payload.get("items", [])
    for it in items:
        post_sle(item_id=it["item_id"], warehouse_id=it["warehouse_id"],
                 qty=Decimal(str(it["qty"])), voucher_type="Opening", voucher_id=None,
                 lot_id=it.get("lot_id"), rate=Decimal(str(it.get("rate",0))))
    return jsonify({"posted": len(items)}), 201


