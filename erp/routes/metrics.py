from flask import Blueprint, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from erp.metrics import QUEUE_LAG, GRAPHQL_REJECTS, GRAPHQL_REJECTS_TOTAL
from erp.db import redis_client

bp = Blueprint("metrics", __name__)

@bp.get("/metrics")
def metrics():
    try:
        depth = float(redis_client.llen("celery"))
        QUEUE_LAG.labels("celery").set(depth)
    except Exception:
        pass
    try:
        GRAPHQL_REJECTS_TOTAL.set(GRAPHQL_REJECTS._value.get())
    except Exception:
        pass
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)