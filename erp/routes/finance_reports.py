"""Finance report skeleton endpoints (ageing buckets, etc.)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("finance_reports_api", __name__, url_prefix="/api/finance/reports")


def _bucket_age(days: int) -> str:
    if days <= 0:
        return "current"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


@bp.get("/ar-ageing")
@require_roles("finance", "admin")
def ar_ageing():
    """Accounts receivable ageing (skeleton)."""

    from erp.models import Invoice  # type: ignore

    org_id = resolve_org_id()
    as_of_raw = request.args.get("as_of")
    as_of = date.fromisoformat(as_of_raw) if as_of_raw else date.today()

    query = Invoice.query
    if hasattr(Invoice, "org_id"):
        query = query.filter_by(org_id=org_id)
    invoices = query.filter(Invoice.total > 0).all()

    buckets: dict[str, Decimal] = {}
    for inv in invoices:
        due_date = getattr(inv, "due_date", None) or getattr(inv, "created_at", as_of)
        delta_days = (as_of - due_date.date() if hasattr(due_date, "date") else as_of - due_date).days
        bucket = _bucket_age(delta_days)
        buckets.setdefault(bucket, Decimal("0"))
        buckets[bucket] += getattr(inv, "open_amount", inv.total)

    response = {k: float(v) for k, v in buckets.items()}
    return jsonify({"as_of": as_of.isoformat(), "buckets": response}), HTTPStatus.OK
