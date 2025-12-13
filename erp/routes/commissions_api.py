from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from erp.extensions import db
from erp.models import Order, User
from erp.security_decorators_phase2 import require_permission
from erp.utils import resolve_org_id

bp = Blueprint("commissions_api", __name__, url_prefix="/api/commissions")


@dataclass(frozen=True)
class MonthRange:
    start: datetime
    end: datetime
    label: str


def _parse_month(month_str: str | None) -> MonthRange:
    """
    month_str format: 'YYYY-MM'
    Commission is computed by settlement month (Order.paid_at), because credit sales are only
    eligible when payment is settled.
    """
    if not month_str:
        now = datetime.now(UTC)
        month_str = f"{now.year:04d}-{now.month:02d}"

    try:
        year_s, month_s = month_str.split("-")
        year = int(year_s)
        month = int(month_s)
        if month < 1 or month > 12:
            raise ValueError
    except Exception:
        raise ValueError("month must be in YYYY-MM format")

    start = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month + 1, 1, tzinfo=UTC)
    return MonthRange(start=start, end=end, label=f"{year:04d}-{month:02d}")


def _commission_amount(total_amount: Decimal, rate: Decimal) -> Decimal:
    try:
        return (total_amount or Decimal("0")) * (rate or Decimal("0"))
    except Exception:
        return Decimal("0")


@bp.get("/summary")
@require_permission("commissions", "view")
def summary():
    """Monthly commission summary by sales rep.

    Query:
      - month=YYYY-MM (optional; default current month)
      - include_zero=1 (optional)
    """
    org_id = resolve_org_id()
    month = _parse_month(request.args.get("month"))

    include_zero = (request.args.get("include_zero") or "").strip() == "1"

    # Eligible commissions: payment settled AND commission_status == 'eligible'
    # Note: Order model sets commission_status='pending' until settlement.
    q = (
        db.session.query(
            Order.ass
