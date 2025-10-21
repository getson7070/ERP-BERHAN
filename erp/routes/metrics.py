from flask import Blueprint, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from erp import redis_client
from erp.metrics import QUEUE_LAG

bp = Blueprint("metrics", __name__)

@bp.get("/metrics")
def metrics():
    try:
        depth = redis_client.llen("celery")
        QUEUE_LAG.labels("celery").set(float(depth))
    except Exception:
        pass
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
