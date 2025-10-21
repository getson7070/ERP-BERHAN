from flask import Blueprint, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from erp import redis_client
from erp.metrics import QUEUE_LAG

bp = Blueprint("metrics", __name__)

@bp.get("/metrics")
def metrics():
    # update queue lag for "celery" right before scraping
    try:
        depth = redis_client.llen("celery")
        QUEUE_LAG.labels("celery").set(depth)
    except Exception:
        pass
    data = generate_latest()
    return Response(data, mimetype=CONTENT_TYPE_LATEST)
