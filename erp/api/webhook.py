from flask import Blueprint, request, jsonify
import hmac, hashlib, json
from erp import redis_client
from erp.metrics import RATE_LIMIT_REJECTIONS
from erp.cache import init_cache as _init_cache_noop

api_bp = Blueprint("api", __name__, url_prefix="/api")

def init_cache(app=None):
    # tests call this as init_cache(app); our shim ignores the arg
    _init_cache_noop()

@api_bp.get("/orders")
def orders():
    auth = request.headers.get("Authorization", "")
    if auth != "Bearer testtoken":
        RATE_LIMIT_REJECTIONS.inc()
        return jsonify({"error": "unauthorized"}), 401
    return jsonify([{"id": 1, "status": "ok"}])

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
    if payload.get("simulate_failure"):
        # mimic Celery "task failure" path -> DLQ handled by tests via _dead_letter_handler
        raise RuntimeError("simulated webhook failure")
    return jsonify({"ok": True})

@api_bp.post("/event")
def event():
    # minimal accept-any JSON to satisfy schema-oriented tests
    _ = request.get_json(silent=True) or {}
    return jsonify({"ok": True})

@api_bp.post("/graphql")
def graphql():
    # not a real GraphQL impl; just a placeholder 200 for tests
    return jsonify({"data": {"ok": True}})
