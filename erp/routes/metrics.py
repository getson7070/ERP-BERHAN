import os
from flask import Blueprint, Response, request
from ..metrics import snapshot

bp = Blueprint("metrics", __name__)

def _auth_ok() -> bool:
    token = os.getenv("METRICS_AUTH_TOKEN", "")
    if not token:
        return True
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {token}"

@bp.get("/metrics")
def metrics():
    if not _auth_ok():
        return Response("unauthorized\n", status=401, mimetype="text/plain; version=0.0.4")
    s = snapshot()
    body = (
        "# HELP app_requests_total Total requests.\n"
        "# TYPE app_requests_total counter\n"
        f"app_requests_total {s.requests}\n"
        "# HELP app_errors_total Total errors.\n"
        "# TYPE app_errors_total counter\n"
        f"app_errors_total {s.errors}\n"
        "# HELP app_cache_hits_total Total cache hits.\n"
        "# TYPE app_cache_hits_total counter\n"
        f"app_cache_hits_total {s.cache_hits}\n"
        "# HELP app_cache_misses_total Total cache misses.\n"
        "# TYPE app_cache_misses_total counter\n"
        f"app_cache_misses_total {s.cache_misses}\n"
        "# HELP app_queue_lag Queue backlog size.\n"
        "# TYPE app_queue_lag gauge\n"
        f"app_queue_lag {s.queue_lag}\n"
    )
    return Response(body, mimetype="text/plain; version=0.0.4")
