"""Integration endpoints for external systems."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from graphql import parse
import graphene

from erp import GRAPHQL_REJECTS, csrf, limiter
from erp.routes.api import token_required
from erp.utils import roles_required

bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")


@bp.post("/events")
@csrf.exempt
@token_required
@roles_required("Admin")
@limiter.limit("20 per minute")
def receive_event():
    """Accept webhook-style events from trusted systems."""
    data = request.get_json() or {}
    if not isinstance(data.get("event"), str) or not isinstance(
        data.get("payload"), dict
    ):
        return jsonify({"error": "invalid schema"}), 400
    return jsonify({"status": "accepted"})


class EventType(graphene.ObjectType):
    name = graphene.String()


class Query(graphene.ObjectType):
    events = graphene.List(EventType)

    def resolve_events(root, info):  # pragma: no cover - simple stub
        return []


schema = graphene.Schema(query=Query)


@bp.post("/graphql")
@csrf.exempt
@token_required
@roles_required("Admin")
@limiter.limit("20 per minute")
def graphql_endpoint():
    data = request.get_json() or {}
    query = data.get("query", "")
    try:
        parse(query)
    except Exception as exc:  # pragma: no cover - validation
        GRAPHQL_REJECTS.inc()
        return jsonify({"errors": [str(exc)]}), 400
    result = schema.execute(query)
    if result.errors:
        return jsonify({"errors": [str(e) for e in result.errors]}), 400
    return jsonify(result.data)
