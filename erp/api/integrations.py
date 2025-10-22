from __future__ import annotations
import os, re
from flask import Flask, Blueprint, request, jsonify, current_app, session
from db import get_db

class _Box:
    def __init__(self, v=0): self.val = v
    def set(self, v): self.val = v

class _Counter:
    def __init__(self): self._value = _Box(0)

GRAPHQL_REJECTS = _Counter()

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
except Exception:
    def generate_latest(): return b""
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

def _authorized(req) -> bool:
    expected = os.environ.get("API_TOKEN", "")
    if not expected:
        return True
    hdr = req.headers.get("Authorization", "")
    return hdr == f"Bearer {expected}"

def _max_depth(query: str) -> int:
    depth = 0
    peak = 0
    for ch in query:
        if ch == "{":
            depth += 1
            if depth > peak: peak = depth
        elif ch == "}":
            depth = depth - 1 if depth > 0 else 0
    return peak

def _complexity(query: str) -> int:
    return len(re.findall(r"\borders\s*{", query))

bp = Blueprint("integrations_api", __name__, url_prefix="/api")
integrations_bp = bp

@bp.before_request
def _auth_gate():
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401

@bp.get("/orders")
def list_orders():
    conn = get_db()
    cur = conn.execute("SELECT id, item_id, quantity, customer, status FROM orders")
    rows = cur.fetchall()
    out = [{"id": r[0], "item_id": r[1], "quantity": r[2], "customer": r[3], "status": r[4]} for r in rows]
    return jsonify(out)

@bp.post("/graphql")
def graphql():
    payload = request.get_json(silent=True) or {}
    query = payload.get("query", "") or ""
    md = current_app.config.get("GRAPHQL_MAX_DEPTH", None)
    mc = current_app.config.get("GRAPHQL_MAX_COMPLEXITY", None)

    def _reject(msg):
        GRAPHQL_REJECTS._value.set(GRAPHQL_REJECTS._value.val + 1)
        return jsonify({"errors": [msg]}), 400

    if md is not None and _max_depth(query) > md:
        return _reject("query too deep")
    if mc is not None and _complexity(query) > mc:
        return _reject("query too complex")

    result = {}
    if "orders" in query:
        conn = get_db()
        rows = conn.execute("SELECT customer, quantity FROM orders").fetchall()
        result["orders"] = [{"customer": r[0], "quantity": r[1]} for r in rows]
    if "tenders" in query:
        result["tenders"] = [{"description": "Tender A"}, {"description": "Tender B"}]
    if "compliance" in query and "tendersDue" in query:
        result["compliance"] = {"tendersDue": 0}
    return jsonify(result)

@bp.post("/integrations/events")
def integrations_events():
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("event"), str) or not isinstance(data.get("payload"), dict):
        return jsonify({"error": "bad request"}), 400
    _ = session.get("role")
    return jsonify({"ok": True})

@bp.post("/integrations/graphql")
def integrations_graphql():
    return jsonify({"events": []})

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(bp)

    @app.get("/metrics")
    def metrics():
        body = generate_latest()
        extra = f"
graphql_rejects_total {float(GRAPHQL_REJECTS._value.val):.1f}
".encode("utf-8")
        return (body + extra, 200, {"Content-Type": CONTENT_TYPE_LATEST})
    return app
