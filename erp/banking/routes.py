"""Banking endpoints integrated with the finance ledger."""
from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import func

from erp.extensions import db
from erp.models import BankTransaction, FinanceAccount, FinanceEntry
from erp.utils import resolve_org_id

from .models import BankAccount, BankStatement, StatementLine

banking_bp = Blueprint("banking", __name__, url_prefix="/banking")


def _ensure_cash_account(org_id: int, account: BankAccount) -> FinanceAccount:
    code = f"BANK-{account.id}"
    ledger = FinanceAccount.query.filter_by(org_id=org_id, code=code).first()
    if ledger is None:
        ledger = FinanceAccount(org_id=org_id, code=code, name=f"Cash - {account.name}", category="asset")
        db.session.add(ledger)
        db.session.flush()
    return ledger


def _account_balance(org_id: int, account: BankAccount) -> Decimal:
    inflow = (
        db.session.query(func.coalesce(func.sum(BankTransaction.amount), 0))
        .filter_by(org_id=org_id, bank_account_id=account.id, direction="inflow")
        .scalar()
    )
    outflow = (
        db.session.query(func.coalesce(func.sum(BankTransaction.amount), 0))
        .filter_by(org_id=org_id, bank_account_id=account.id, direction="outflow")
        .scalar()
    )
    return account.initial_balance + Decimal(inflow or 0) - Decimal(outflow or 0)


@banking_bp.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    """Create and list bank accounts scoped to the active organisation."""

    org_id = resolve_org_id()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

        currency = (data.get("currency") or "ETB").upper()
        initial_balance = Decimal(str(data.get("initial_balance", "0")))
        account = BankAccount(
            org_id=org_id,
            name=name,
            currency=currency,
            account_number=data.get("account_number"),
            initial_balance=initial_balance,
        )
        db.session.add(account)
        db.session.flush()
        _ensure_cash_account(org_id, account)
        db.session.commit()
        return jsonify({"id": account.id}), HTTPStatus.CREATED

    rows = BankAccount.query.filter_by(org_id=org_id).order_by(BankAccount.name).all()
    payload = [
        {
            "id": row.id,
            "name": row.name,
            "currency": row.currency,
            "balance": float(_account_balance(org_id, row)),
        }
        for row in rows
    ]
    return jsonify(payload), HTTPStatus.OK


@banking_bp.post("/transactions")
@login_required
def record_transaction():
    """Record an inflow/outflow and link it to the finance ledger."""

    data = request.get_json(silent=True) or {}
    org_id = resolve_org_id()
    account_id = data.get("bank_account_id")
    direction = (data.get("direction") or "").lower()
    amount = data.get("amount")
    if not account_id or direction not in {"inflow", "outflow"} or amount is None:
        return (
            jsonify({"error": "bank_account_id, direction and amount are required"}),
            HTTPStatus.BAD_REQUEST,
        )

    account = BankAccount.query.filter_by(id=account_id, org_id=org_id).first_or_404()
    entry_amount = Decimal(str(amount))
    transaction = BankTransaction(
        org_id=org_id,
        bank_account_id=account.id,
        direction=direction,
        amount=entry_amount,
        reference=data.get("reference"),
    )
    db.session.add(transaction)
    db.session.flush()

    cash_account = _ensure_cash_account(org_id, account)
    direction_entry = "debit" if direction == "inflow" else "credit"
    db.session.add(
        FinanceEntry(
            org_id=org_id,
            account_id=cash_account.id,
            bank_transaction_id=transaction.id,
            amount=entry_amount,
            direction=direction_entry,
            memo=data.get("memo"),
        )
    )
    db.session.commit()
    return jsonify({"id": transaction.id}), HTTPStatus.CREATED


@banking_bp.post("/statements")
@login_required
def create_statement():
    """Create a bank statement and persist optional line items."""

    data = request.get_json(silent=True) or {}
    org_id = resolve_org_id()

    bank_account_id = data.get("bank_account_id")
    if not bank_account_id:
        return jsonify({"error": "bank_account_id is required"}), HTTPStatus.BAD_REQUEST

    account = BankAccount.query.filter_by(id=bank_account_id, org_id=org_id).first_or_404()
    statement = BankStatement(
        bank_account_id=account.id,
        closing_balance=_account_balance(org_id, account),
    )
    db.session.add(statement)
    db.session.flush()

    for line_item in data.get("lines", []):
        amount = line_item.get("amount")
        if amount is None:
            db.session.rollback()
            return jsonify({"error": "each line requires 'amount'"}), HTTPStatus.BAD_REQUEST

        db.session.add(
            StatementLine(
                statement_id=statement.id,
                amount=Decimal(str(amount)),
                description=line_item.get("description"),
                reference=line_item.get("reference"),
            )
        )

    db.session.commit()
    return jsonify({"id": statement.id}), HTTPStatus.CREATED


@banking_bp.get("/accounts/<int:account_id>/transactions")
@login_required
def list_transactions(account_id: int):
    """Return the transaction history for a bank account."""

    org_id = resolve_org_id()
    BankAccount.query.filter_by(id=account_id, org_id=org_id).first_or_404()
    transactions = (
        BankTransaction.query.filter_by(org_id=org_id, bank_account_id=account_id)
        .order_by(BankTransaction.posted_at.desc())
        .all()
    )
    payload = [
        {
            "id": txn.id,
            "direction": txn.direction,
            "amount": float(txn.amount),
            "reference": txn.reference,
            "posted_at": txn.posted_at.isoformat(),
        }
        for txn in transactions
    ]
    return jsonify(payload)



