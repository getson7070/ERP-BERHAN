from types import SimpleNamespace
from flask import Flask, jsonify, request, session, redirect, url_for
import os, json, time

from .metrics import (
    GRAPHQL_REJECTS, RATE_LIMIT_REJECTIONS, QUEUE_LAG, AUDIT_CHAIN_BROKEN,
    OLAP_EXPORT_SUCCESS as _OLAP_EXPORT_SUCCESS
)
OLAP_EXPORT_SUCCESS = _OLAP_EXPORT_SUCCESS

class _MemRedis:
    def __init__(self): self.kv = {}
    def delete(self, key): self.kv.pop(key, None)
    def _as_list(self, key):
        v = self.kv.get(key)
        if isinstance(v, list):
            return v
        # if it existed as a set or anything else, migrate to a list
        lst = list(v) if isinstance(v, (set, tuple)) else ([] if v is None else [v])
        self.kv[key] = lst
        return lst
    def rpush(self, key, *vals):
        lst = self._as_list(key)
        for v in vals:
            lst.append(v)
        return len(lst)
    def lrange(self, key, start, end):
        data = list(self._as_list(key))
        return data[start:(end+1 if end != -1 else None)]
    def llen(self, key):
        return len(self._as_list(key))
    def sadd(self, key, val):
        s = self.kv.get(key)
        if not isinstance(s, set):
            s = set()
            self.kv[key] = s
        s.add(val)
    def sismember(self, key, val):
        s = self.kv.get(key)
        return isinstance(s, set) and (val in s)

redis_client = _MemRedis()
_IDEM_SEEN = set()

def _dead_letter_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, **extra):
    payload = {
        "sender": getattr(sender, "name", str(sender)),
        "task_id": task_id, "exception": str(exception),
        "args": list(args or []), "kwargs": dict(kwargs or {}),
        "ts": time.time(),
    }
    js = json.dumps(payload)
    # push to both names; tests read "dead_letter"
    redis_client.rpush("dead_letter", js)
    redis_client.rpush("dead-letter", js)

socketio = SimpleNamespace(emit=lambda *a, **k: None)

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    from .routes.health import bp as health_bp
    from .routes.metrics import bp as metrics_bp
    from .routes.analytics import bp as analytics_bp
    from .routes.bots import bp as bots_bp
    from .routes.finance import bp as finance_bp
    from .routes.integration import bp as integration_bp
    from .routes.recall import bp as recall_bp
    from .api.webhook import api_bp
    from .api.integrations import bp as integrations_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(bots_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(integration_bp)
    app.register_blueprint(recall_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(integrations_bp)

    @app.route("/idem", methods=["POST"])
    def _idem():
        key = request.headers.get("Idempotency-Key")
        if not key:
            return jsonify({"error": "missing Idempotency-Key"}), 400
        if key in _IDEM_SEEN:
            return jsonify({"error": "duplicate"}), 409
        _IDEM_SEEN.add(key)
        return jsonify({"ok": True})

    @app.get("/set_language/<lang>")
    def set_language(lang):
        session["lang"] = lang
        return redirect(url_for("dashboard"))

    @app.get("/dashboard")
    def dashboard():
        lang = session.get("lang", "en")
        opts = "".join([
            f'<option value="en"{" selected" if lang=="en" else ""}>English</option>',
            f'<option value="am"{" selected" if lang=="am" else ""}>Amharic</option>',
        ])
        return f'<!doctype html><html lang="{lang}"><body><select id="lang-select">{opts}</select></body></html>'

    return app

__all__ = [
    "create_app", "socketio", "redis_client", "_dead_letter_handler",
    "GRAPHQL_REJECTS", "RATE_LIMIT_REJECTIONS", "QUEUE_LAG", "AUDIT_CHAIN_BROKEN", "OLAP_EXPORT_SUCCESS",
]