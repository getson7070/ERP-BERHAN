"""Finance blueprint exposing ledger and journal operations."""
from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from sqlalchemy import case, func

from erp.extensions import db
from erp.models import FinanceAccount, FinanceEntry
from erp.utils import resolve_org_id
from erp.security import require_login, require_roles


# API blueprint mounted under /api/finance
finance_bp = Blueprint("finance_api", __name__, url_prefix="/api/finance")


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


@finance_bp.get("/health")
@require_roles("finance", "admin")
def health() -> Any:
    """Simple health check with basic account count."""
    return jsonify({"ok": True, "accounts": FinanceAccount.query.count()})


@finance_bp.get("/ledger")
@require_roles("finance", "admin")
def list_accounts():
    """Return all ledger accounts with current balances."""

    org_id = resolve_org_id()
    accounts = (
        FinanceAccount.query.filter_by(org_id=org_id, is_active=True)
        .order_by(FinanceAccount.code)
        .all()
    )
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


@finance_bp.post("/ledger")
@require_roles("finance", "admin")
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


@finance_bp.post("/journal")
@require_roles("finance", "admin")
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


bp = finance_bp

__all__ = ["bp"]
