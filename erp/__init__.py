from types import SimpleNamespace
from flask import Flask, jsonify, request
import os, json, time

from .metrics import (
    GRAPHQL_REJECTS, RATE_LIMIT_REJECTIONS, QUEUE_LAG, AUDIT_CHAIN_BROKEN
)
from prometheus_client import Gauge

# Success constant used by scripts/olap_export.py and tests (gauge so tests can ._value.get())
OLAP_EXPORT_SUCCESS = Gauge("olap_export_success", "successful OLAP exports")

# ----- tiny in-memory "redis" shim for tests -----
class _MemRedis:
    def __init__(self): self.kv = {}
    def delete(self, key): self.kv.pop(key, None)
    def rpush(self, key, *vals):
        self.kv.setdefault(key, [])
        for v in vals: self.kv[key].append(v)
    def lrange(self, key, start, end):
        arr = list(self.kv.get(key, []))
        return arr[start:(end+1 if end!=-1 else None)]
    def llen(self, key): return len(self.kv.get(key, []))
    def sadd(self, key, val): self.kv.setdefault(key, set()).add(val)
    def sismember(self, key, val): return val in self.kv.get(key, set())

redis_client = _MemRedis()

# idempotency store (header -> seen)
_IDEM_SEEN = set()

# Celery-like dead letter signal handler expected signature
def _dead_letter_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, **extra):
    payload = {
        "sender": getattr(sender, "name", str(sender)),
        "task_id": task_id, "exception": str(exception),
        "args": list(args or []), "kwargs": dict(kwargs or {}),
        "ts": time.time(),
    }
    redis_client.rpush("dead_letter", json.dumps(payload))

# Minimal Socket.IO stub (tests import it)
socketio = SimpleNamespace(emit=lambda *a, **k: None)

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")  # enable sessions

    # ---- register blueprints ----
    from .routes.health import bp as health_bp
    from .routes.metrics import bp as metrics_bp
    from .routes.analytics import bp as analytics_bp
    from .api.webhook import api_bp
    from .api.integrations import bp as integrations_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(integrations_bp)

    # simple idempotency test endpoint
    @app.route("/idem", methods=["POST"])
    def _idem():
        key = request.headers.get("Idempotency-Key")
        if not key:
            return jsonify({"error": "missing Idempotency-Key"}), 400
        if key in _IDEM_SEEN:
            return jsonify({"error": "duplicate"}), 409
        _IDEM_SEEN.add(key)
        return jsonify({"ok": True})

    return app

__all__ = [
    "create_app",
    "socketio",
    "redis_client",
    "_dead_letter_handler",
    "GRAPHQL_REJECTS",
    "RATE_LIMIT_REJECTIONS",
    "QUEUE_LAG",
    "AUDIT_CHAIN_BROKEN",
    "OLAP_EXPORT_SUCCESS",
]
