from flask import Blueprint, jsonify, request

bp = Blueprint("mfa", __name__, url_prefix="/mfa")

@bp.get("/setup")
def setup():
    # scaffold endpoint; replace with real QR/provisioning later
    return jsonify({"ok": True, "message": "MFA scaffold ready"}), 200

@bp.post("/verify")
def verify():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code") or request.form.get("code")
    ok = bool(code) and str(code).isdigit() and len(str(code)) == 6
    return (jsonify({"verified": True}), 200) if ok else (jsonify({"verified": False}), 400)
