"""Self-service report builder endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from erp.security import require_roles, mfa_required
from sqlalchemy import func

from erp.extensions import db
from erp.models import (
    AnalyticsEvent,
    CrmLead,
    FinanceEntry,
    Inventory,
    MaintenanceTicket,
    Order,
    SupplyChainShipment,
)
from erp.utils import resolve_org_id

bp = Blueprint("report_builder", __name__, url_prefix="/reports")


@bp.get("/builder")
@login_required
@require_roles("admin", "analytics", "management")
@mfa_required
def builder_view():
    return render_template("report_builder.html", user=current_user)


@bp.post("/run")
@login_required
@require_roles("admin", "analytics", "management")
@mfa_required
def run_report():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    period = payload.get("period", "all")

    orders = Order.query.filter_by(organization_id=org_id).all()
    finance_credits = (
        db.session.query(func.coalesce(func.sum(FinanceEntry.amount), 0))
        .filter_by(org_id=org_id, direction="credit")
        .scalar()
    )
    finance_debits = (
        db.session.query(func.coalesce(func.sum(FinanceEntry.amount), 0))
        .filter_by(org_id=org_id, direction="debit")
        .scalar()
    )
    lead_breakdown = (
        db.session.query(CrmLead.status, func.count())
        .filter_by(org_id=org_id)
        .group_by(CrmLead.status)
        .all()
    )
    hotspots = (
        db.session.query(AnalyticsEvent.location_label, func.count())
        .filter(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.location_label.isnot(None),
        )
        .group_by(AnalyticsEvent.location_label)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    shipments = SupplyChainShipment.query.filter_by(org_id=org_id).count()
    low_stock = (
        Inventory.query.filter(Inventory.org_id == org_id, Inventory.quantity <= 5).count()
    )
    open_tickets = (
        MaintenanceTicket.query.filter_by(org_id=org_id, status="open").count()
    )

    report = {
        "period": period,
        "orders": {
            "total": len(orders),
            "by_status": {status: sum(1 for o in orders if o.status == status) for status in {o.status for o in orders}},
        },
        "finance": {
            "credits": float(finance_credits or 0),
            "debits": float(finance_debits or 0),
            "net": float((finance_credits or 0) - (finance_debits or 0)),
        },
        "crm": {status: count for status, count in lead_breakdown},
        "operations": {
            "low_stock_items": low_stock,
            "open_tickets": open_tickets,
            "shipments": shipments,
        },
        "geo": [
            {"label": label, "count": count}
            for label, count in hotspots
            if label
        ],
    }

    return jsonify(report)


__all__ = ["bp", "builder_view", "run_report"]
