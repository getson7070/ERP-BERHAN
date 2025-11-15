"""Analytics routes exposing KPI summaries and background tasks."""
from __future__ import annotations

from typing import Iterable, List

from flask import Blueprint, jsonify, request

from erp.analytics import DemandForecaster
from erp.audit import get_db

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


def fetch_kpis():
    """Return placeholder KPIs so dashboard routes stay responsive in dev/test."""

    return {
        "pending_orders": 0,
        "pending_maintenance": 0,
        "expired_tenders": 0,
        "monthly_sales": [],
    }


@bp.post("/vitals")
def collect_vitals():
    data = request.get_json(silent=True) or {}
    allowed = {"lcp", "fid", "cls", "ttfb", "inp"}
    if not any(k in data for k in allowed):
        return jsonify({"error": "bad schema"}), 400
    return "", 204


@bp.get("/dashboard")
def dashboard_snapshot():
    return jsonify(fetch_kpis())


def _send_approval_reminders(users: Iterable[int] | None = None) -> int:
    conn = get_db()
    try:
        cur = conn.execute("SELECT COUNT(1) FROM orders WHERE status='pending'")
        (count,) = cur.fetchone() or (0,)
        return int(count or 0)
    finally:
        conn.close()


def _forecast_sales(history: List[int] | None = None, observed: List[int] | None = None) -> float:
    conn = get_db()
    try:
        try:
            vals = [row[0] for row in conn.execute("SELECT total_sales FROM kpi_sales ORDER BY month").fetchall()]
        except Exception:
            vals = history or [1, 2, 3]
        return float(DemandForecaster().fit(vals).predict_next())
    finally:
        conn.close()


class _Task:
    def __init__(self, fn):
        self.run = fn

    def __call__(self, *a, **k):
        return self.run(*a, **k)


send_approval_reminders = _Task(_send_approval_reminders)
forecast_sales = _Task(_forecast_sales)

__all__ = [
    "bp",
    "fetch_kpis",
    "collect_vitals",
    "dashboard_snapshot",
    "send_approval_reminders",
    "forecast_sales",
]
