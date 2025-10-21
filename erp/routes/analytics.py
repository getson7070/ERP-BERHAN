from flask import Blueprint, request, jsonify
from typing import Iterable, List, Dict, Any
from erp.analytics import retrain_and_predict, DemandForecaster
from erp.audit import get_db

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@bp.post("/vitals")
def collect_vitals():
    data = request.get_json(silent=True) or {}
    allowed = {"lcp", "fid", "cls", "ttfb", "inp"}
    if not any(k in data for k in allowed):
        return jsonify({"error": "bad schema"}), 400
    return ("", 204)

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
            vals = history or [1,2,3]
        return float(DemandForecaster().fit(vals).predict_next())
    finally:
        conn.close()

class _Task:
    def __call__(self, *a, **k): return self.run(*a, **k)
    def run(self, *a, **k): raise NotImplementedError

class send_approval_reminders(_Task):
    def run(self, users: Iterable[int] | None = None) -> int:
        return _send_approval_reminders(users)

class forecast_sales(_Task):
    def run(self, history: List[int] | None = None, observed: List[int] | None = None) -> float:
        return _forecast_sales(history, observed)
