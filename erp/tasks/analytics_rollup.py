"""Nightly analytics rollups into AnalyticsFact."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from celery import shared_task
from sqlalchemy import func

from erp.extensions import db
from erp.models import AnalyticsFact, AnalyticsMetric, MaintenanceWorkOrder, StockLedgerEntry


def _upsert_fact(org_id: int, metric_key: str, ts_date: date, value: Decimal, **dims) -> None:
    fact = AnalyticsFact.query.filter_by(
        org_id=org_id,
        metric_key=metric_key,
        ts_date=ts_date,
        warehouse_id=dims.get("warehouse_id"),
        region=dims.get("region"),
        user_id=dims.get("user_id"),
        client_id=dims.get("client_id"),
        item_id=dims.get("item_id"),
    ).first()

    if fact:
        fact.value = value
        return

    fact = AnalyticsFact(
        org_id=org_id,
        metric_key=metric_key,
        ts_date=ts_date,
        value=value,
        warehouse_id=dims.get("warehouse_id"),
        region=dims.get("region"),
        user_id=dims.get("user_id"),
        client_id=dims.get("client_id"),
        item_id=dims.get("item_id"),
    )
    db.session.add(fact)


@shared_task(name="erp.tasks.analytics.rollup_daily")
def rollup_daily() -> None:
    """Compute daily KPIs from source modules and persist into AnalyticsFact."""

    ts_date = date.today() - timedelta(days=1)
    metrics = AnalyticsMetric.query.filter(AnalyticsMetric.is_active.is_(True)).all()
    org_ids = sorted({metric.org_id for metric in metrics})

    for org_id in org_ids:
        stock_moves = (
            db.session.query(func.count(StockLedgerEntry.id))
            .filter(
                StockLedgerEntry.org_id == org_id,
                func.date(StockLedgerEntry.created_at) == ts_date,
            )
            .scalar()
            or 0
        )
        _upsert_fact(org_id, "inventory.daily_stock_moves", ts_date, Decimal(stock_moves))

        downtime_sum = (
            db.session.query(func.coalesce(func.sum(MaintenanceWorkOrder.downtime_minutes), 0))
            .filter(
                MaintenanceWorkOrder.org_id == org_id,
                MaintenanceWorkOrder.status == "completed",
                func.date(MaintenanceWorkOrder.completed_at) == ts_date,
            )
            .scalar()
            or 0
        )
        _upsert_fact(org_id, "maintenance.total_downtime_minutes", ts_date, Decimal(downtime_sum))

    db.session.commit()
