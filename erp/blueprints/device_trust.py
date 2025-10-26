from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

device_bp = Blueprint("device", __name__, url_prefix="/api/device")

def _engine():
    url = (current_app.config.get("SQLALCHEMY_DATABASE_URI")
           or current_app.config["DATABASE_URL"])
    return create_engine(url, pool_pre_ping=True)

@device_bp.post("/trust")
def check_trust():
    fp = (request.json or {}).get("fingerprint")
    if not fp:
        return jsonify({"trusted": False, "role": "client"}), 400

    sql = text("""
        SELECT td.approved, td.expires_at, u.role
        FROM trusted_devices td
        JOIN users u ON u.id = td.user_id
        WHERE td.fingerprint = :fp
        LIMIT 1
    """)
    with _engine().connect() as conn:
        row = conn.execute(sql, {"fp": fp}).mappings().first()

    if not row:
        return jsonify({"trusted": False, "role": "client"}), 200

    if row["expires_at"] and row["expires_at"] < datetime.utcnow():
        return jsonify({"trusted": False, "role": "client"}), 200

    return jsonify({
        "trusted": bool(row["approved"]),
        "role": row["role"] or "client"
    }), 200

@device_bp.post("/register")
def register_device():
    # This endpoint expects your auth layer to set current user id in a header.
    # Replace with your actual current user resolver if you have one.
    uid = request.headers.get("X-User-Id")
    data = request.json or {}
    fp = data.get("fingerprint")
    name = data.get("device_name", "")
    if not uid or not fp:
        return jsonify({"error": "missing user or fingerprint"}), 400

    # upsert (unique fingerprint)
    upsert = text("""
        INSERT INTO trusted_devices (user_id, fingerprint, device_name, approved, registered_at, last_seen, expires_at)
        VALUES (:uid, :fp, :name, true, NOW(), NOW(), NOW() + INTERVAL '365 days')
        ON CONFLICT (fingerprint) DO UPDATE
           SET user_id = EXCLUDED.user_id,
               device_name = EXCLUDED.device_name,
               approved = true,
               last_seen = NOW(),
               expires_at = NOW() + INTERVAL '365 days'
        RETURNING id;
    """)
    with _engine().connect() as conn:
        conn.execute(upsert, {"uid": int(uid), "fp": fp, "name": name})
        conn.commit()
    return jsonify({"ok": True}), 200

# alias for dynamic importer
bp = device_bp

