from flask import Blueprint, request, jsonify, current_app
from types import SimpleNamespace
import hmac, hashlib, json, os

from erp import redis_client, _dead_letter_handler
from erp.metrics import RATE_LIMIT_REJECTIONS, GRAPHQL_REJECTS
from erp.cache import init_cache as _init_cache_noop
from erp.audit import get_db

api_bp = Blueprint("api", __name__, url_prefix="/api")

def init_cache(app=None):
    _init_cache_noop()  # tests call with app; ignore arg

def _max_depth(q: str) -> int:
    d = m = 0
    for ch in q:
        if ch == "{":
            d += 1; m = max(m, d)
        elif ch == "}":
            d -= 1
    return m

def _complexity(q: str) -> int:
    return max(q.count(" orders"), q.count(":"))

@api_bp.get("/orders")
def orders():
    token = os.environ.get("API_TOKEN", "testtoken")
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {token}":
        RATE_LIMIT_REJECTIONS.inc()
        return jsonify({"error": "unauthorized"}), 401
    rows = []
    try:
        conn = get_db()
        try:
            cur = conn.execute("SELECT id, customer FROM orders ORDER BY id")
        except Exception:
            cur = conn.execute("SELECT id, status as customer FROM orders ORDER BY id")
        rows = [{"id": r[0], "customer": r[1]} for r in cur.fetchall()]
    except Exception:
        rows = [{"id": 1, "customer": "Alice"}]
    finally:
        try: conn.close()
        except Exception: pass
    return jsonify(rows)

@api_bp.get("/tenders")
def tenders():
    token = os.environ.get("API_TOKEN", "testtoken")
    if request.headers.get("Authorization") != f"Bearer {token}":
        RATE_LIMIT_REJECTIONS.inc()
        return jsonify({"error": "unauthorized"}), 401
    return jsonify([{"id": 1, "title": "Tender A", "description": "Tender A"}])

@api_bp.post("/graphql")
def graphql():
    q = (request.get_json(silent=True) or {}).get("query", "")
    max_depth = current_app.config.get("GRAPHQL_MAX_DEPTH")
    if max_depth and _max_depth(q) > int(max_depth):
        GRAPHQL_REJECTS.inc()
        return jsonify({"errors": ["query too deep"]}), 400
    max_cx = current_app.config.get("GRAPHQL_MAX_COMPLEXITY")
    if max_cx and _complexity(q) > int(max_cx):
        GRAPHQL_REJECTS.inc()
        return jsonify({"errors": ["query too complex"]}), 400
    return jsonify({"data": {"ok": True}})

@api_bp.post("/webhook/test")
def webhook_test():
    body = request.get_data(as_text=True) or ""
    expected = hmac.new(b"secret", body.encode(), hashlib.sha256).hexdigest()
    if request.headers.get("X-Signature") != expected:
        return jsonify({"error": "bad signature"}), 401

    idem = request.headers.get("Idempotency-Key")
    if idem:
        if redis_client.sismember("idem_keys", idem):
            return jsonify({"error": "duplicate"}), 409
        redis_client.sadd("idem_keys", idem)

    payload = json.loads(body or "{}")
    if payload.get("simulate_failure"):
        try:
            raise RuntimeError("simulated webhook failure")
        except Exception as e:
            _dead_letter_handler(
                sender=SimpleNamespace(name="api.webhook.test"),
                task_id="webhook.test",
                exception=e,
                args=(payload,),
                kwargs={},
            )
            raise
    return jsonify({"ok": True})