"""General ledger endpoints with double-entry enforcement."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy.orm import joinedload

from erp.extensions import db
from erp.models import GLJournalEntry, GLJournalLine, FinanceAuditLog
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("finance_gl_api", __name__, url_prefix="/api/finance")


def _parse_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def _serialize_line(line: GLJournalLine) -> dict[str, Any]:
    return {
        "id": line.id,
        "account_code": line.account_code,
        "account_name": line.account_name,
        "debit": float(line.debit),
        "credit": float(line.credit),
        "debit_base": float(line.debit_base),
        "credit_base": float(line.credit_base),
        "source_type": line.source_type,
        "source_id": line.source_id,
    }


def _serialize_entry(entry: GLJournalEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "org_id": entry.org_id,
        "journal_code": entry.journal_code,
        "reference": entry.reference,
        "description": entry.description,
        "currency": entry.currency,
        "base_currency": entry.base_currency,
        "fx_rate": float(entry.fx_rate),
        "document_date": entry.document_date.isoformat(),
        "posting_date": entry.posting_date.isoformat(),
        "status": entry.status,
        "created_at": entry.created_at.isoformat(),
        "created_by_id": entry.created_by_id,
        "posted_at": entry.posted_at.isoformat() if entry.posted_at else None,
        "posted_by_id": entry.posted_by_id,
        "lines": [_serialize_line(l) for l in entry.lines],
    }


@bp.post("/journal")
@require_roles("finance", "admin")
def create_journal():
    """Create a draft journal entry with lines; does NOT post it yet."""

    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    currency = (payload.get("currency") or "ETB").upper()
    base_currency = (payload.get("base_currency") or currency).upper()
    fx_rate = _parse_decimal(payload.get("fx_rate") or "1")

    doc_date_raw = payload.get("document_date") or payload.get("posting_date")
    if not doc_date_raw:
        return jsonify({"error": "document_date or posting_date is required"}), HTTPStatus.BAD_REQUEST

    doc_date = date.fromisoformat(doc_date_raw)
    posting_date_raw = payload.get("posting_date") or doc_date_raw
    posting_date = date.fromisoformat(posting_date_raw)

    lines_payload = payload.get("lines") or []
    if not lines_payload:
        return jsonify({"error": "at least one line is required"}), HTTPStatus.BAD_REQUEST

    entry = GLJournalEntry(
        org_id=org_id,
        journal_code=(payload.get("journal_code") or "GENERAL").upper(),
        reference=(payload.get("reference") or "").strip() or None,
        description=(payload.get("description") or "").strip() or None,
        currency=currency,
        base_currency=base_currency,
        fx_rate=fx_rate,
        document_date=doc_date,
        posting_date=posting_date,
        status="draft",
        created_by_id=getattr(current_user, "id", None),
    )

    for raw in lines_payload:
        account_code = (raw.get("account_code") or "").strip()
        if not account_code:
            return jsonify({"error": "account_code is required for each line"}), HTTPStatus.BAD_REQUEST

        debit = _parse_decimal(raw.get("debit"))
        credit = _parse_decimal(raw.get("credit"))
        if debit < 0 or credit < 0:
            return jsonify({"error": "debit/credit must not be negative"}), HTTPStatus.BAD_REQUEST
        if debit == 0 and credit == 0:
            return jsonify({"error": "each line must have debit or credit"}), HTTPStatus.BAD_REQUEST

        debit_base = debit * fx_rate
        credit_base = credit * fx_rate

        line = GLJournalLine(
            org_id=org_id,
            account_code=account_code,
            account_name=(raw.get("account_name") or "").strip() or None,
            debit=debit,
            credit=credit,
            debit_base=debit_base,
            credit_base=credit_base,
            source_type=(raw.get("source_type") or "").strip() or None,
            source_id=raw.get("source_id"),
        )
        entry.lines.append(line)

    try:
        entry.require_balanced()
    except ValueError as exc:  # pragma: no cover - user facing validation
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    db.session.add(entry)
    db.session.commit()
    return jsonify(_serialize_entry(entry)), HTTPStatus.CREATED


@bp.post("/journal/<int:entry_id>/post")
@require_roles("finance", "admin")
def post_journal(entry_id: int):
    """Post a draft journal entry; once posted it becomes immutable."""

    from datetime import datetime as _dt

    org_id = resolve_org_id()
    entry = (
        GLJournalEntry.query.filter_by(org_id=org_id, id=entry_id)
        .options(joinedload(GLJournalEntry.lines))
        .with_for_update()
        .first_or_404()
    )

    if entry.status != "draft":
        return (
            jsonify({"error": f"only draft entries can be posted (current: {entry.status})"}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        entry.require_balanced()
    except ValueError as exc:  # pragma: no cover - user facing validation
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    entry.status = "posted"
    entry.posted_at = _dt.utcnow()
    entry.posted_by_id = getattr(current_user, "id", None)

    log = FinanceAuditLog(
        org_id=org_id,
        event_type="JOURNAL_POSTED",
        entity_type="GL_JOURNAL_ENTRY",
        entity_id=entry.id,
        payload={"journal_code": entry.journal_code, "reference": entry.reference},
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(log)

    db.session.commit()
    return jsonify(_serialize_entry(entry)), HTTPStatus.OK
