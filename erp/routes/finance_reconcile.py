"""Bank reconciliation endpoints including imports and auto-matching."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy.orm import joinedload

from erp.extensions import db
from erp.models import (
    BankStatement,
    BankStatementLine,
    GLJournalEntry,
    GLJournalLine,
    FinanceAuditLog,
)
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("finance_reconcile_api", __name__, url_prefix="/api/finance/reconcile")


def _parse_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


@bp.post("/bank-statements/import")
@require_roles("finance", "admin")
def import_bank_statement():
    """Import a bank statement (manual upload or API)."""

    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    bank_account_code = (payload.get("bank_account_code") or "").strip()
    if not bank_account_code:
        return jsonify({"error": "bank_account_code is required"}), HTTPStatus.BAD_REQUEST

    period_start = date.fromisoformat(payload["period_start"])
    period_end = date.fromisoformat(payload["period_end"])
    opening_balance = _parse_decimal(payload.get("opening_balance"))
    closing_balance = _parse_decimal(payload.get("closing_balance"))

    stmt = BankStatement(
        org_id=org_id,
        bank_account_code=bank_account_code,
        currency=(payload.get("currency") or "ETB").upper(),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        source=(payload.get("source") or "UPLOAD").upper(),
        external_reference=(payload.get("external_reference") or "").strip() or None,
        created_by_id=getattr(current_user, "id", None),
        statement_date=period_end,
    )

    for raw in payload.get("lines") or []:
        tx_date = date.fromisoformat(raw["tx_date"])
        line = BankStatementLine(
            org_id=org_id,
            tx_date=tx_date,
            description=(raw.get("description") or "").strip() or None,
            amount=_parse_decimal(raw.get("amount")),
            balance=_parse_decimal(raw.get("balance")),
            reference=(raw.get("reference") or "").strip() or None,
        )
        stmt.lines.append(line)

    db.session.add(stmt)
    db.session.commit()

    return jsonify({"statement_id": stmt.id}), HTTPStatus.CREATED


@bp.post("/bank-statements/<int:statement_id>/auto-match")
@require_roles("finance", "admin")
def auto_match(statement_id: int):
    """Attempt to match bank statement lines to posted GL entries."""

    org_id = resolve_org_id()
    stmt = (
        BankStatement.query.filter_by(org_id=org_id, id=statement_id)
        .options(joinedload(BankStatement.lines))
        .first_or_404()
    )

    bank_account_code = stmt.bank_account_code
    min_date = stmt.period_start
    max_date = stmt.period_end

    gl_lines = (
        GLJournalLine.query.join(GLJournalEntry, GLJournalLine.journal_entry_id == GLJournalEntry.id)
        .filter(
            GLJournalLine.org_id == org_id,
            GLJournalEntry.org_id == org_id,
            GLJournalEntry.status == "posted",
            GLJournalLine.account_code == bank_account_code,
            GLJournalEntry.posting_date >= min_date,
            GLJournalEntry.posting_date <= max_date,
        )
        .all()
    )

    by_amount: dict[Decimal, list[GLJournalLine]] = {}
    for line in gl_lines:
        amt = abs(line.net)
        by_amount.setdefault(amt, []).append(line)

    matched_count = 0

    for line in stmt.lines:
        if line.matched:
            continue

        amt = abs(line.amount)
        candidates = by_amount.get(amt) or []
        if not candidates:
            continue

        candidate = None
        for l in candidates:
            if not any(
                bs_line.matched_journal_entry_id == l.journal_entry_id for bs_line in stmt.lines
            ):
                candidate = l
                break
        if candidate is None:
            continue

        line.matched = True
        line.matched_journal_entry_id = candidate.journal_entry_id
        line.matched_at = datetime.utcnow()
        line.matched_by_id = getattr(current_user, "id", None)
        matched_count += 1

    if matched_count:
        log = FinanceAuditLog(
            org_id=org_id,
            event_type="BANK_AUTOMATCH",
            entity_type="BANK_STATEMENT",
            entity_id=stmt.id,
            payload={"matched_count": matched_count},
            created_by_id=getattr(current_user, "id", None),
        )
        db.session.add(log)

    db.session.commit()
    return jsonify({"matched": matched_count}), HTTPStatus.OK
