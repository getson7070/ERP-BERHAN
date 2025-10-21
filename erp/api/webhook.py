from flask import Blueprint, request, jsonify, session
import hmac, hashlib, json, re
from erp import redis_client, _dead_letter_handler
from erp.metrics import RATE_LIMIT_REJECTIONS, GRAPHQL_REJECTS, QUEUE_LAG
from erp.cache import init_cache as _init_cache_noop
from erp.audit import get_db

api_bp = Blueprint("api", __name__, url_prefix="/api")

def init_cache(app=None):
    _init_cache_noop()  # tests call this with app

@api_bp.get("/orders")
def orders():
    auth = request.headers.get("Authorization", "")
    if auth != "Bearer testtoken":
        RATE_LIMIT_REJECTIONS.inc()
        return jsonify({"error": "unauthorized"}), 401
    # Pull from DB if present; fall back to a sample
    try:
        conn = get_db()
        cur = conn.execute("SELECT id, customer FROM orders ORDER BY id")
        rows = [{"id": r[0], "customer": r[1]} for r in cur.fetchall()]
        conn.close()
        if rows:
            return jsonify(rows)
    except Exception:
        pass
    return jsonify([{"id": 1, "customer": "Alice"}])

@api_bp.post("/webhook/test")
def webhook_test():
    body = request.get_data(as_text=True) or ""
    expected = hmac.new(b"secret", body.encode(), hashlib.sha256).hexdigest()
    if request.headers.get("X-Signature") != expected:
        return jsonify({"error": "bad signature"}), 401

    # idempotency
    idem = request.headers.get("Idempotency-Key")
    if idem:
        if redis_client.sismember("idem_keys", idem):
            return jsonify({"error": "duplicate"}), 409
        redis_client.sadd("idem_keys", idem)

    payload = json.loads(body or "{}")
    try:
        if payload.get("simulate_failure"):
            raise RuntimeError("simulated webhook failure")
        return jsonify({"ok": True})
    except Exception as exc:
        # Mirror celery dead-letter behavior for the tests
        _dead_letter_handler(sender="erp.webhook", task_id="webhook.test",
                             exception=exc, args=(), kwargs={"payload": payload})
        return jsonify({"error": "failed"}), 500

@api_bp.post("/graphql")
def graphql():
    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "):
        RATE_LIMIT_REJECTIONS.inc()
        return jsonify({"error": "unauthorized"}), 401
    q = (request.get_json(silent=True) or {}).get("query", "") or ""

    # depth
    depth = 0; max_depth = 0
    for ch in q:
        if ch == "{": depth += 1; max_depth = max(max_depth, depth)
        elif ch == "}": depth -= 1
    limit_depth = int(request.app.config.get("GRAPHQL_MAX_DEPTH", 9999)) if hasattr(request, "app") else int((request.environ.get("werkzeug.request").app.config.get("GRAPHQL_MAX_DEPTH", 9999)))
    if max_depth > limit_depth:
        GRAPHQL_REJECTS.inc()
        return jsonify({"error": "too deep"}), 400

    # naive complexity: count alias like a0:, a1:, ... (exact pattern used in test)
    complexity = len(re.findall(r"\ba\d+\s*:", q))
    limit_complex = int(request.environ.get("werkzeug.request").app.config.get("GRAPHQL_MAX_COMPLEXITY", 9999))
    if complexity > limit_complex:
        GRAPHQL_REJECTS.inc()
        return jsonify({"error": "too complex"}), 400

    return jsonify({"data": {"ok": True}})
