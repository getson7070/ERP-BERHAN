from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request

from erp.extensions import db
from erp.models import User, UserMFA
from erp.security_decorators_phase2 import require_permission
from erp.services.mfa_service import (
    disable_mfa,
    enable_mfa,
    generate_backup_codes,
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
)
from erp.utils import resolve_org_id

bp = Blueprint("admin_console_api", __name__, url_prefix="/api/admin")


@bp.get("/users")
@require_permission("users", "view")
def list_users():
    org_id = resolve_org_id()
    users = User.query.filter_by(org_id=org_id).order_by(User.id.desc()).limit(500).all()
    out = []
    for u in users:
        out.append(
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": bool(u.is_active),
                "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
            }
        )
    return jsonify(out), HTTPStatus.OK


@bp.post("/users/<int:user_id>/roles/grant")
@require_permission("users", "manage_roles")
def grant_user_role(user_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role:
        return jsonify({"error": "role required"}), HTTPStatus.BAD_REQUEST

    user = User.query.filter_by(org_id=org_id, id=user_id).first()
    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    user.grant_role(role)
    db.session.commit()
    return jsonify({"ok": True}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/roles/revoke")
@require_permission("users", "manage_roles")
def revoke_user_role(user_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role:
        return jsonify({"error": "role required"}), HTTPStatus.BAD_REQUEST

    user = User.query.filter_by(org_id=org_id, id=user_id).first()
    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    user.revoke_role(role)
    db.session.commit()
    return jsonify({"ok": True}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/deactivate")
@require_permission("users", "deactivate")
def deactivate_user(user_id: int):
    org_id = resolve_org_id()
    user = User.query.filter_by(org_id=org_id, id=user_id).first()
    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND
    user.is_active = False
    db.session.commit()
    return jsonify({"ok": True}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/reactivate")
@require_permission("users", "reactivate")
def reactivate_user(user_id: int):
    org_id = resolve_org_id()
    user = User.query.filter_by(org_id=org_id, id=user_id).first()
    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND
    user.is_active = True
    db.session.commit()
    return jsonify({"ok": True}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/mfa/init")
@require_permission("users", "mfa_manage")
def init_mfa(user_id: int):
    org_id = resolve_org_id()
    user = User.query.filter_by(org_id=org_id, id=user_id).first()
    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    secret = generate_totp_secret()
    uri = get_totp_uri(user.email, secret)
    return jsonify({"secret": secret, "uri": uri}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/mfa/enable")
@require_permission("users", "mfa_manage")
def enable_user_mfa(user_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    secret = (payload.get("secret") or "").strip()
    code = (payload.get("code") or "").strip()

    if not secret or not code:
        return jsonify({"error": "secret and code required"}), HTTPStatus.BAD_REQUEST

    if not verify_totp(secret, code):
        return jsonify({"error": "invalid_totp"}), HTTPStatus.BAD_REQUEST

    enable_mfa(org_id, user_id, secret)
    codes = generate_backup_codes(org_id, user_id)
    return jsonify({"status": "enabled", "backup_codes": codes}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/mfa/disable")
@require_permission("users", "mfa_manage")
def disable_user_mfa(user_id: int):
    org_id = resolve_org_id()
    disable_mfa(org_id, user_id)
    return jsonify({"status": "disabled"}), HTTPStatus.OK
