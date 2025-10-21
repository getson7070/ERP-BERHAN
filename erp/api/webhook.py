import hmac, hashlib, json, os
from flask import Blueprint, request, jsonify
from ..cache import cache_get, cache_set
from ..dlq import push_dead_letter

bp = Blueprint("api", __name__, url_prefix="/api")

def _verify_signature(raw: bytes) -> bool:
    secret = os.getenv("WEBHOOK_SECRET", "")
    if not secret:
        return True
    sig = request.headers.get("X-Signature", "")
    mac = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, mac)

@bp.route("/webhook/<source>", methods=["POST"])
def webhook(source: str):
    idem = request.headers.get("Idempotency-Key")
    if idem:
        if cache_get(f"idempotency:{idem}"):
            return jsonify({"status": "duplicate"}), 409
        cache_set(f"idempotency:{idem}", True)

    raw = request.get_data()
    if not _verify_signature(raw):
        push_dead_letter({"source": source, "reason": "bad_signature", "body": raw.decode("utf-8", "ignore")})
        return jsonify({"error": "signature"}), 401

    payload = request.get_json(silent=True) or {}
    return jsonify({"status": "ok", "source": source, "received": bool(payload)}), 200
