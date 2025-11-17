"""Finance blueprint exposing ledger and journal operations."""
from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import case, func

from erp.extensions import db
from erp.models import FinanceAccount, FinanceEntry
from erp.utils import resolve_org_id
"""Finance API blueprint exposing ledger, journal, and bank transaction operations.

This module consolidates previous finance blueprints into a single API.  It
provides endpoints for listing and creating ledger accounts, posting balanced
journal entries (debits and credits), and retrieving account balances.  All
endpoints are scoped to the current organisation and require authentication.
"""
from __future__ import annotations


def _account_balance(account: FinanceAccount) -> float:
    totals = (
        db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (FinanceEntry.direction == "debit", FinanceEntry.amount),
                        else_=-FinanceEntry.amount,
                    )
                ),
                0,
            )
        )
        .filter(FinanceEntry.account_id == account.id)
        .scalar()
    )
    return float(totals or 0)



def _account_balance(account: FinanceAccount) -> float:
    totals = (
        db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (FinanceEntry.direction == "debit", FinanceEntry.amount),
                        else_=-FinanceEntry.amount,
                    )
                ),
                0,
            )
        )
        .filter(FinanceEntry.account_id == account.id)
        .scalar()
    )
    return float(totals or 0)


@finance_api_bp.get("/health")
def health():
    return jsonify({"ok": True, "accounts": FinanceAccount.query.count()})


@finance_api_bp.get("/ledger")
@login_required
def list_accounts():
    """Return all ledger accounts with current balances."""

    org_id = resolve_org_id()
    accounts = FinanceAccount.query.filter_by(org_id=org_id, is_active=True).order_by(FinanceAccount.code).all()
    payload = [
        {
            "id": account.id,
            "code": account.code,
            "name": account.name,
            "category": account.category,
            "balance": _account_balance(account),
        }
        for account in accounts
    ]
    return jsonify(payload)


@finance_api_bp.post("/ledger")
@login_required
def create_account():
    """Create a new general ledger account."""

    data = request.get_json(silent=True) or {}
    org_id = resolve_org_id()
    code = (data.get("code") or "").strip().upper()
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "asset").lower()
    if not code or not name:
        return jsonify({"error": "code and name are required"}), HTTPStatus.BAD_REQUEST
    if category not in {"asset", "liability", "equity", "income", "expense"}:
        return jsonify({"error": "invalid category"}), HTTPStatus.BAD_REQUEST

    account = FinanceAccount(org_id=org_id, code=code, name=name, category=category)
    db.session.add(account)
    db.session.commit()
    return jsonify({"id": account.id}), HTTPStatus.CREATED


@finance_api_bp.post("/journal")
@login_required
def post_journal():
    """Create balancing debit and credit entries."""

    data = request.get_json(silent=True) or {}
    org_id = resolve_org_id()
    debits = data.get("debits", [])
    credits = data.get("credits", [])
    memo = data.get("memo")

    if not debits or not credits:
        return jsonify({"error": "debits and credits are required"}), HTTPStatus.BAD_REQUEST

    def _normalise(entries):
        normalised = []
        for item in entries:
            account_id = item.get("account_id")
            amount = item.get("amount")
            if not account_id or amount is None:
                raise ValueError("account_id and amount are required")
            normalised.append((int(account_id), Decimal(str(amount))))
        return normalised

    try:
        normalised_debits = _normalise(debits)
        normalised_credits = _normalise(credits)
    except ValueError as exc:  # pragma: no cover - defensive branch
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    total_debits = sum(amount for _, amount in normalised_debits)
    total_credits = sum(amount for _, amount in normalised_credits)
    if total_debits != total_credits:
        return jsonify({"error": "journal is not balanced"}), HTTPStatus.BAD_REQUEST

    created_ids: list[int] = []
    for account_id, amount in normalised_debits:
        entry = FinanceEntry(
            org_id=org_id,
            account_id=account_id,
            amount=amount,
            direction="debit",
            memo=memo,
        )
        db.session.add(entry)
        db.session.flush()
        created_ids.append(entry.id)

    for account_id, amount in normalised_credits:
        entry = FinanceEntry(
            org_id=org_id,
            account_id=account_id,
            amount=amount,
            direction="credit",
            memo=memo,
        )
        db.session.add(entry)
        db.session.flush()
        created_ids.append(entry.id)

    db.session.commit()
    return jsonify({"entries": created_ids}), HTTPStatus.CREATED

from decimal import Decimal
from http import HTTPStatus
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import case, func

from erp.extensions import db
from erp.models import FinanceAccount, FinanceEntry, BankTransaction
from erp.utils import resolve_org_id


finance_bp = Blueprint("finance", __name__, url_prefix="/api/finance")


def _account_balance(account: FinanceAccount) -> float:
    totals = (
        db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (FinanceEntry.direction == "debit", FinanceEntry.amount),
                        else_=-FinanceEntry.amount,
                    )
                ),
                0,
            )
        )
        .filter(FinanceEntry.account_id == account.id)
        .scalar()
    )
    return float(totals or 0)


def _serialize_account(account: FinanceAccount) -> Dict[str, Any]:
    return {
        "id": account.id,
        "code": account.code,
        "name": account.name,
        "category": account.category,
        "balance": _account_balance(account),
    }


def _serialize_entry(entry: FinanceEntry) -> Dict[str, Any]:
    return {
        "id": entry.id,
        "account_id": entry.account_id,
        "amount": float(entry.amount),
        "direction": entry.direction,
        "memo": entry.memo,
        "posted_at": entry.posted_at.isoformat(),
        "order_id": entry.order_id,
        "bank_transaction_id": entry.bank_transaction_id,
    }


@finance_bp.get("/health")
def health() -> Any:
    return jsonify({"ok": True, "accounts": FinanceAccount.query.count()})


@finance_bp.route("/ledger", methods=["GET", "POST"])
@login_required
def ledger():
    """List ledger accounts or create a new one."""
    org_id = resolve_org_id()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        code = (data.get("code") or "").strip().upper()
        name = (data.get("name") or "").strip()
        category = (data.get("category") or "asset").lower()
        if not code or not name:
            return jsonify({"error": "code and name are required"}), HTTPStatus.BAD_REQUEST
        if category not in {"asset", "liability", "equity", "income", "expense"}:
            return jsonify({"error": "invalid category"}), HTTPStatus.BAD_REQUEST
        account = FinanceAccount(org_id=org_id, code=code, name=name, category=category)
        db.session.add(account)
        db.session.commit()
        return jsonify({"id": account.id}), HTTPStatus.CREATED
    # GET list
    accounts = (
        FinanceAccount.query.filter_by(org_id=org_id, is_active=True)
        .order_by(FinanceAccount.code)
        .all()
    )
    return jsonify([_serialize_account(a) for a in accounts])


@finance_bp.route("/journal", methods=["POST"])
@login_required
def post_journal() -> Any:
    """Create a balanced journal entry consisting of debit and credit lines."""
    data = request.get_json(silent=True) or {}
    org_id = resolve_org_id()
    debits = data.get("debits", [])
    credits = data.get("credits", [])
    memo = data.get("memo")
    if not debits or not credits:
        return jsonify({"error": "debits and credits are required"}), HTTPStatus.BAD_REQUEST
    def _normalise(entries):
        normalised = []
        for item in entries:
            account_id = item.get("account_id")
            amount = item.get("amount")
            if not account_id or amount is None:
                raise ValueError("account_id and amount are required")
            normalised.append((int(account_id), Decimal(str(amount))))
        return normalised
    try:
        normalised_debits = _normalise(debits)
        normalised_credits = _normalise(credits)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
    total_debits = sum(amount for _, amount in normalised_debits)
    total_credits = sum(amount for _, amount in normalised_credits)
    if total_debits != total_credits:
        return jsonify({"error": "journal is not balanced"}), HTTPStatus.BAD_REQUEST
    created_ids: list[int] = []
    for account_id, amount in normalised_debits:
        entry = FinanceEntry(
            org_id=org_id,
            account_id=account_id,
            amount=amount,
            direction="debit",
            memo=memo,
        )
        db.session.add(entry)
        db.session.flush()
        created_ids.append(entry.id)
    for account_id, amount in normalised_credits:
        entry = FinanceEntry(
            org_id=org_id,
            account_id=account_id,
            amount=amount,
            direction="credit",
            memo=memo,
        )
        db.session.add(entry)
        db.session.flush()
        created_ids.append(entry.id)
    db.session.commit()
    return jsonify({"entries": created_ids}), HTTPStatus.CREATED


@finance_bp.get("/entries")
@login_required
def list_entries() -> Any:
    """Return journal entries for the current organisation."""
    org_id = resolve_org_id()
    entries = (
        FinanceEntry.query.filter_by(org_id=org_id)
        .order_by(FinanceEntry.posted_at.desc())
        .all()
    )
    return jsonify([_serialize_entry(e) for e in entries])


@finance_bp.get("/entries/<int:entry_id>")
@login_required
def entry_detail(entry_id: int) -> Any:
    """Retrieve a single journal entry."""
    org_id = resolve_org_id()
    entry = FinanceEntry.query.filter_by(id=entry_id, org_id=org_id).first()
    if entry is None:
        return jsonify({"error": "entry not found"}), HTTPStatus.NOT_FOUND
    return jsonify(_serialize_entry(entry))


@finance_bp.get("/accounts/<int:account_id>/transactions")
@login_required
def account_transactions(account_id: int) -> Any:
    """List bank transactions for a given account."""
    org_id = resolve_org_id()
    transactions = (
        BankTransaction.query.filter_by(bank_account_id=account_id, org_id=org_id)
        .order_by(BankTransaction.posted_at.desc())
        .all()
    )
    return jsonify([
        {
            "id": t.id,
            "direction": t.direction,
            "amount": float(t.amount),
            "reference": t.reference,
            "posted_at": t.posted_at.isoformat(),
        }
        for t in transactions
    ])

bp = finance_bp

__all__ = ["bp"]
