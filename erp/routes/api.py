from flask import Blueprint, jsonify, request, abort, current_app
from functools import wraps
import re
from db import get_db
import os
import hmac
import hashlib
from erp import TOKEN_ERRORS, limiter
from erp.utils import idempotency_key_required

bp = Blueprint('api', __name__, url_prefix='/api')

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        expected = current_app.config.get('API_TOKEN') or os.environ.get('API_TOKEN')
        if expected and token != expected:
            TOKEN_ERRORS.inc()
            abort(401)
        return f(*args, **kwargs)
    return wrapper

@bp.get('/orders')
@token_required
@limiter.limit('50 per minute')
def list_orders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, item_id, quantity, customer, status FROM orders')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    orders = [
        {
            'id': r[0],
            'item_id': r[1],
            'quantity': r[2],
            'customer': r[3],
            'status': r[4]
        }
        for r in rows
    ]
    return jsonify(orders)

# GraphQL endpoint
import graphene

class OrderType(graphene.ObjectType):
    id = graphene.Int()
    item_id = graphene.Int()
    quantity = graphene.Int()
    customer = graphene.String()
    status = graphene.String()

class Query(graphene.ObjectType):
    orders = graphene.List(OrderType)

    def resolve_orders(root, info):
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, item_id, quantity, customer, status FROM orders')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [OrderType(id=r[0], item_id=r[1], quantity=r[2], customer=r[3], status=r[4]) for r in rows]

schema = graphene.Schema(query=Query)

@bp.post('/graphql')
@token_required
@limiter.limit('50 per minute')
def graphql_endpoint():
    data = request.get_json() or {}
    query = data.get('query', '')
    max_depth = current_app.config.get('GRAPHQL_MAX_DEPTH', 5)
    depth = 0
    deepest = 0
    for ch in query:
        if ch == '{':
            depth += 1
            deepest = max(deepest, depth)
        elif ch == '}':
            depth -= 1
    if deepest > max_depth:
        abort(400, 'query too deep')
    max_complexity = current_app.config.get('GRAPHQL_MAX_COMPLEXITY', 1000)
    if len(re.findall(r"[A-Za-z0-9_]+", query)) > max_complexity:
        abort(400, 'query too complex')
    result = schema.execute(query)
    if result.errors:
        return jsonify({'errors': [str(e) for e in result.errors]}), 400
    return jsonify(result.data)

@bp.post('/webhook/<source>')
@token_required
@idempotency_key_required
@limiter.limit('20 per minute')
def webhook(source):
    secret = current_app.config.get('WEBHOOK_SECRET')
    signature = request.headers.get('X-Signature', '')
    expected = hmac.new(
        (secret or '').encode(), request.data, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        abort(401)
    payload = request.get_json() or {}
    return jsonify({'status': 'received', 'source': source, 'payload': payload})
