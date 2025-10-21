from flask import Blueprint, current_app, request, Response
from ..metrics import QUEUE_LAG, Gauge, render_prometheus
from ..cache import redis_client
from ..analytics import kpi_staleness_seconds

bp = Blueprint("metrics", __name__)

@bp.get("/metrics")
def metrics():
    token = current_app.config.get("METRICS_AUTH_TOKEN")
    if token:
        auth = request.headers.get("Authorization","")
        if not (auth.startswith("Bearer ") and auth.split(" ",1)[1]==token):
            return Response("Unauthorized", status=401)

    # queue lag
    try:
        n = redis_client.llen("celery")
    except Exception:
        n = 0
    QUEUE_LAG.labels("celery").set(n)

    # KPI freshness
    Gauge("kpi_sales_mv_age_seconds").set(kpi_staleness_seconds())

    return Response(render_prometheus(), mimetype="text/plain")
