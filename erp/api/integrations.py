from flask import Blueprint, request, jsonify, session, current_app
import os

bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")

def _authorized() -> bool:
    token = os.environ.get("API_TOKEN", current_app.config.get("API_TOKEN", "secret"))
    return request.headers.get("Authorization") == f"Bearer {token}"

@bp.post("/events")
def events():
    if not _authorized() or session.get("role") != "Admin":
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("event"), str):
        return jsonify({"error": "bad schema"}), 400
    return jsonify({"ok": True})

@bp.post("/graphql")
def gql():
    if not _authorized() or session.get("role") != "Admin":
        return jsonify({"error": "forbidden"}), 403
    return jsonify({"events": []})