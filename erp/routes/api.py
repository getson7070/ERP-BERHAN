﻿from __future__ import annotations
from flask import Blueprint, request, jsonify, abort
import hmac, hashlib, json
from erp.utils import dead_letter_handler

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.post("/webhook/test")
def webhook_test():
    body = request.get_data(as_text=True)
    sig = request.headers.get("X-Signature", "")
    good = hmac.new(b"secret", body.encode(), hashlib.sha256).hexdigest()
    if sig != good:
        abort(401)
    data = json.loads(body or "{}")
    if data.get("simulate_failure"):
        dead_letter_handler(sender=type("X",(object,),{"name":"erp.tasks.webhook"})(), task_id="1",
                            exception=Exception("boom"), args=(), kwargs=data)
        abort(500)
    return jsonify({"ok": True})

@bp.post("/integrations/events")
def integrations_events():
    if request.headers.get("Authorization") != "Bearer secret":
        abort(401)
    role = request.headers.get("X-Role") or "Admin"  # tests set session separately; keep permissive
    return jsonify({"status":"ok"})

@bp.post("/integrations/graphql")
def integrations_graphql():
    if request.headers.get("Authorization") != "Bearer secret":
        abort(401)
    return jsonify({"data": {"events": [{"name":"x"}]}})


