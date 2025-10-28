"""Module: banking/routes.py — audit-added docstring. Refine with precise purpose when convenient."""
# erp/banking/routes.py
from http import HTTPStatus
from flask import Blueprint, jsonify, request
from flask_login import login_required

from erp.extensions import db
from .models import BankAccount, BankStatement, StatementLine

banking_bp = Blueprint("banking", __name__, url_prefix="/banking")


@banking_bp.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    """
    GET: List bank accounts.
    POST: Create a new bank account. Body: {"name": "...", "currency": "ETB" (optional)}
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or {}

        name = data.get("name")
        if not name:
            return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

        currency = data.get("currency", "ETB")
        obj = BankAccount(name=name, currency=currency)
        db.session.add(obj)
        db.session.commit()
        return jsonify({"id": str(obj.id)}), HTTPStatus.CREATED

    rows = BankAccount.query.order_by(BankAccount.name).all()
    payload = [
        {"id": str(r.id), "name": r.name, "currency": r.currency}
        for r in rows
    ]
    return jsonify(payload), HTTPStatus.OK


@banking_bp.post("/statements")
@login_required
def create_statement():
    """
    Create a bank statement with optional lines.
    Body: {
      "bank_account_id": "<uuid>",
      "lines": [{"amount": 123.45, "description": "optional"}]
    }
    """
    data = request.get_json(silent=True) or {}

    bank_account_id = data.get("bank_account_id")
    if not bank_account_id:
        return jsonify({"error": "bank_account_id is required"}), HTTPStatus.BAD_REQUEST

    st = BankStatement(bank_account_id=bank_account_id)
    db.session.add(st)
    db.session.flush()  # get st.id

    for line_item in data.get("lines", []):
        # E741 fix: use a descriptive variable name (line_item), not 'l'
        amount = line_item.get("amount")
        if amount is None:
            db.session.rollback()
            return jsonify({"error": "each line requires 'amount'"}), HTTPStatus.BAD_REQUEST

        db.session.add(
            StatementLine(
                statement_id=st.id,
                amount=amount,
                description=line_item.get("description"),
            )
        )

    db.session.commit()
    return jsonify({"id": str(st.id)}), HTTPStatus.CREATED



