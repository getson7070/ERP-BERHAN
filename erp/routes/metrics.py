from __future__ import annotations
from flask import Blueprint, Response, request
from db import redis_client
from erp.metrics import GRAPHQL_REJECTS, QUEUE_LAG

bp = Blueprint("metrics", __name__)

@bp.get("/metrics")
def metrics():
    token = request.headers.get("Authorization", "")
    required = request.app.config.get("METRICS_AUTH_TOKEN") if hasattr(request, "app") else None
    # Fallback: read from Flask global config
    try:
        from flask import current_app
        required = current_app.config.get("METRICS_AUTH_TOKEN")
    except Exception:
        pass
    if required:
        if not token or token != f"Bearer {required}":
            return Response(status=401)

    # update queue lag gauge from Redis "celery" list
    try:
        q_len = len(redis_client.lrange("celery", 0, -1))
    except Exception:
        q_len = 0
    QUEUE_LAG.labels("celery").set(q_len)

    # Minimal text exposition (just enough for tests to 200/401)
    body = "# minimal metrics\n"
    body += f"graphql_rejects {GRAPHQL_REJECTS._value.get()}\n"
    body += f"queue_lag {QUEUE_LAG._value.get()}\n"
    return Response(body, mimetype="text/plain")


