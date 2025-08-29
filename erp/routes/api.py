from flask import Blueprint, jsonify, request, abort, current_app
from functools import wraps
from db import get_db, redis_client
import os
import hmac
import hashlib
import json
import graphene
from graphql import parse
from erp import (
    TOKEN_ERRORS,
    limiter,
    GRAPHQL_REJECTS,
    csrf,
)
from erp.utils import idempotency_key_required

bp = Blueprint("api", __name__, url_prefix="/api")


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        expected = current_app.config.get("API_TOKEN") or os.environ.get("API_TOKEN")
        if expected and token != expected:
            TOKEN_ERRORS.inc()
            abort(401)
        return f(*args, **kwargs)

    return wrapper


@bp.get("/orders")
@token_required
@limiter.limit("50 per minute")
def list_orders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, item_id, quantity, customer, status FROM orders")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    orders = [
        {
            "id": r[0],
            "item_id": r[1],
            "quantity": r[2],
            "customer": r[3],
            "status": r[4],
        }
        for r in rows
    ]
    return jsonify(orders)


@bp.get("/tenders")
@token_required
@limiter.limit("50 per minute")
def list_tenders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, description, workflow_state FROM tenders")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "description": r[1], "state": r[2]} for r in rows])


@bp.get("/compliance_reports")
@token_required
@limiter.limit("20 per minute")
def compliance_reports():
    """Return simple compliance metrics."""
    return jsonify({"tenders_due": 0, "orders_pending": 0})


class OrderType(graphene.ObjectType):
    id = graphene.Int()
    item_id = graphene.Int()
    quantity = graphene.Int()
    customer = graphene.String()
    status = graphene.String()


class TenderType(graphene.ObjectType):
    id = graphene.Int()
    description = graphene.String()
    state = graphene.String()


class ComplianceReportType(graphene.ObjectType):
    tenders_due = graphene.Int()
    orders_pending = graphene.Int()


class Query(graphene.ObjectType):
    orders = graphene.List(OrderType)
    tenders = graphene.List(TenderType)
    compliance = graphene.Field(ComplianceReportType)

    def resolve_orders(root, info):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, item_id, quantity, customer, status FROM orders")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            OrderType(id=r[0], item_id=r[1], quantity=r[2], customer=r[3], status=r[4])
            for r in rows
        ]

    def resolve_tenders(root, info):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, description, workflow_state FROM tenders")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [TenderType(id=r[0], description=r[1], state=r[2]) for r in rows]

    def resolve_compliance(root, info):
        return ComplianceReportType(tenders_due=0, orders_pending=0)


schema = graphene.Schema(query=Query)


@bp.post("/graphql")
@csrf.exempt
@token_required
@limiter.limit("50 per minute")
def graphql_endpoint():
    data = request.get_json() or {}
    query = data.get("query", "")
    try:
        ast = parse(query)
    except Exception as exc:
        GRAPHQL_REJECTS.inc()
        return jsonify({"errors": [str(exc)]}), 400

    def analyze(node, depth=0):
        max_depth = depth
        complexity = 0
        if getattr(node, "selection_set", None):
            depth += 1
            max_depth = depth
            for sel in node.selection_set.selections:
                d, c = analyze(sel, depth)
                max_depth = max(max_depth, d)
                complexity += c
        else:
            complexity = 1
        return max_depth, complexity

    total_depth = 0
    total_complexity = 0
    for definition in ast.definitions:
        d, c = analyze(definition, 0)
        total_depth = max(total_depth, d)
        total_complexity += c
    max_depth = current_app.config.get("GRAPHQL_MAX_DEPTH", 5)
    if total_depth > max_depth:
        GRAPHQL_REJECTS.inc()
        return jsonify({"errors": ["query too deep"]}), 400
    max_complexity = current_app.config.get("GRAPHQL_MAX_COMPLEXITY", 1000)
    if total_complexity > max_complexity:
        GRAPHQL_REJECTS.inc()
        return jsonify({"errors": ["query too complex"]}), 400
    result = schema.execute(query)
    if result.errors:
        return jsonify({"errors": [str(e) for e in result.errors]}), 400
    return jsonify(result.data)


@bp.post("/webhook/<source>")
@token_required
@idempotency_key_required
@limiter.limit("20 per minute")
def webhook(source):
    secret = current_app.config.get("WEBHOOK_SECRET")
    signature = request.headers.get("X-Signature")
    if not secret:
        current_app.logger.error("WEBHOOK_SECRET not configured")
        abort(500)
    if not signature:
        abort(401)
    expected = hmac.new(secret.encode(), request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        abort(401)
    try:
        payload = request.get_json() or {}
        if payload.get("simulate_failure"):
            raise RuntimeError("simulated failure")
        return jsonify({"status": "received", "source": source, "payload": payload})
    except Exception as exc:
        redis_client.lpush(
            "dead_letter",
            json.dumps({"task": "api.webhook", "source": source, "error": str(exc)}),
        )
        raise
