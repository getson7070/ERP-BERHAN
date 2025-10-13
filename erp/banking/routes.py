
from flask import Blueprint, request, jsonify
from flask_login import login_required
from erp.extensions import db
from .models import BankAccount, BankStatement, StatementLine

banking_bp = Blueprint("banking", __name__, url_prefix="/banking")

@banking_bp.route("/accounts", methods=["GET","POST"])
@login_required
def accounts():
    if request.method == "POST":
        data = request.get_json() or {}
        obj = BankAccount(name=data["name"], currency=data.get("currency","ETB"))
        db.session.add(obj); db.session.commit()
        return jsonify({"id": str(obj.id)}), 201
    rows = BankAccount.query.order_by(BankAccount.name).all()
    return jsonify([{"id": str(r.id), "name": r.name, "currency": r.currency} for r in rows])

@banking_bp.post("/statements")
@login_required
def create_statement():
    data = request.get_json() or {}
    st = BankStatement(bank_account_id=data["bank_account_id"])
    db.session.add(st); db.session.flush()
    for l in data.get("lines", []):
        db.session.add(StatementLine(statement_id=st.id, amount=l["amount"], description=l.get("description")))
    db.session.commit()
    return jsonify({"id": str(st.id)}), 201
