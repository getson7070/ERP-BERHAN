from flask import Blueprint, request, jsonify, session

bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")

def _authorized(required="secret"):
    return request.headers.get("Authorization") == f"Bearer {required}" and session.get("role") == "Admin"

@bp.post("/events")
def events():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    _ = request.get_json(silent=True) or {}
    return jsonify({"ok": True})

@bp.post("/graphql")
def gql():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    _ = request.get_json(silent=True) or {}
    return jsonify({"data": {"events": [{"name": "order_created"}]}})
