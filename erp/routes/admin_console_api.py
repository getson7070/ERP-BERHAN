from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import User, UserMFA
from erp.security import require_roles
from erp.services.mfa_service import (
    disable_mfa,
    enable_mfa,
    generate_backup_codes,
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
)
from erp.services.role_service import grant_role_to_user, list_role_names, revoke_role_from_user
from erp.services.session_service import revoke_all_sessions_for_user
from erp.utils import resolve_org_id

bp = Blueprint("admin_console_api", __name__, url_prefix="/api/admin")


def _serialize_user(user: User, org_id: int) -> dict[str, object]:
    mfa = UserMFA.query.filter_by(org_id=org_id, user_id=user.id).first()
    return {
        "id": user.id,
        "email": getattr(user, "email", None),
        "username": getattr(user, "username", None),
        "full_name": getattr(user, "full_name", None),
        "is_active": getattr(user, "is_active", True),
        "roles": sorted(list_role_names(user)),
        "mfa_enabled": bool(mfa and mfa.is_enabled),
    }


@bp.get("/users")
@require_roles("admin")
def list_users():
    org_id = resolve_org_id()
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([_serialize_user(u, org_id) for u in users]), HTTPStatus.OK


@bp.post("/users/<int:user_id>/roles/grant")
@require_roles("admin")
def grant_user_role(user_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role:
        return jsonify({"error": "role required"}), HTTPStatus.BAD_REQUEST

    try:
        grant_role_to_user(org_id=org_id, user_id=user_id, role_key=role, acting_user=current_user)
    except PermissionError as exc:  # superadmin required
        return jsonify({"error": str(exc)}), HTTPStatus.FORBIDDEN
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return jsonify({"status": "granted", "role": role.lower()}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/roles/revoke")
@require_roles("admin")
def revoke_user_role(user_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role:
        return jsonify({"error": "role required"}), HTTPStatus.BAD_REQUEST

    try:
        revoke_role_from_user(org_id=org_id, user_id=user_id, role_key=role, acting_user=current_user)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return jsonify({"status": "revoked", "role": role.lower()}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/deactivate")
@require_roles("admin")
def deactivate_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    revoke_all_sessions_for_user(user_id, getattr(current_user, "id", None))
    db.session.commit()
    return jsonify({"status": "deactivated"}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/reactivate")
@require_roles("admin")
def reactivate_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    return jsonify({"status": "reactivated"}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/mfa/init")
@require_roles("admin")
def init_mfa(user_id: int):
    user = User.query.get_or_404(user_id)
    secret = generate_totp_secret()
    uri = get_totp_uri(user.email or f"user{user.id}@erp", secret)
    return jsonify({"secret": secret, "uri": uri}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/mfa/enable")
@require_roles("admin")
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
@require_roles("admin")
def disable_user_mfa(user_id: int):
    org_id = resolve_org_id()
    disable_mfa(org_id, user_id)
    return jsonify({"status": "disabled"}), HTTPStatus.OK
