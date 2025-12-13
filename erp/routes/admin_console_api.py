from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from erp.extensions import db
from erp.models import (
    ClientAccount,
    ClientRegistration,
    Institution,
    User,
)
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


# --------------------------
# Users (existing)
# --------------------------

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


# --------------------------
# C2: Client Onboarding Approvals (NEW, critical)
# --------------------------

@bp.get("/client-registrations")
@require_permission("clients", "approve")
def list_client_registrations():
    org_id = resolve_org_id()
    status = (request.args.get("status") or "pending").strip().lower()
    q = ClientRegistration.query.filter_by(org_id=org_id)
    if status in {"pending", "approved", "rejected"}:
        q = q.filter_by(status=status)
    regs = q.order_by(ClientRegistration.id.desc()).limit(500).all()

    out = []
    for r in regs:
        out.append(
            {
                "id": r.id,
                "uuid": r.uuid,
                "status": r.status,
                "tin": r.tin,
                "institution_name": r.institution_name,
                "institution_type": r.institution_type,
                "contact_name": r.contact_name,
                "contact_position": r.contact_position,
                "email": r.email,
                "phone": r.phone,
                "region": r.region,
                "zone": r.zone,
                "city": r.city,
                "subcity": r.subcity,
                "woreda": r.woreda,
                "kebele": r.kebele,
                "street": r.street,
                "house_number": r.house_number,
                "notes": r.notes,
                "decided_by": r.decided_by,
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
            }
        )
    return jsonify(out), HTTPStatus.OK


@bp.post("/client-registrations/<string:reg_uuid>/approve")
@require_permission("clients", "approve")
def approve_client_registration(reg_uuid: str):
    org_id = resolve_org_id()
    reg = ClientRegistration.query.filter_by(org_id=org_id, uuid=reg_uuid).first()
    if reg is None:
        return jsonify({"error": "not_found"}), HTTPStatus.NOT_FOUND
    if reg.status != "pending":
        return jsonify({"error": "not_pending", "status": reg.status}), HTTPStatus.CONFLICT
    if not reg.password_hash:
        return jsonify({"error": "missing_password_hash"}), HTTPStatus.CONFLICT

    # 1) Create or fetch Institution by TIN (TIN unique per org)
    inst = Institution.query.filter_by(org_id=org_id, tin=reg.tin).first()
    if inst is None:
        inst = Institution(
            org_id=org_id,
            tin=reg.tin,
            legal_name=reg.institution_name,
            institution_type=reg.institution_type,
            region=reg.region,
            zone=reg.zone,
            city=reg.city,
            subcity=reg.subcity,
            woreda=reg.woreda,
            kebele=reg.kebele,
            street=reg.street,
            house_number=reg.house_number,
            notes=reg.notes,
        )
        db.session.add(inst)
        db.session.flush()

    # 2) Create client account for this contact
    existing = ClientAccount.query.filter_by(org_id=org_id, email=reg.email.lower()).first()
    if existing:
        return jsonify({"error": "client_account_email_exists"}), HTTPStatus.CONFLICT

    account = ClientAccount(
        org_id=org_id,
        institution_id=inst.id,
        email=reg.email.lower(),
        phone=reg.phone,
        contact_name=reg.contact_name,
        contact_position=reg.contact_position,
        password_hash=reg.password_hash,
        is_active=True,
        is_approved=True,
    )
    db.session.add(account)

    # 3) Mark registration approved
    reg.status = "approved"
    reg.decided_by = getattr(getattr(request, "user", None), "id", None) or None  # safe fallback
    reg.updated_at = datetime.now(UTC) if hasattr(reg, "updated_at") else None

    db.session.commit()

    return jsonify({"ok": True, "institution_id": inst.id, "client_account_id": account.id}), HTTPStatus.OK


@bp.post("/client-registrations/<string:reg_uuid>/reject")
@require_permission("clients", "approve")
def reject_client_registration(reg_uuid: str):
    org_id = resolve_org_id()
    reg = ClientRegistration.query.filter_by(org_id=org_id, uuid=reg_uuid).first()
    if reg is None:
        return jsonify({"error": "not_found"}), HTTPStatus.NOT_FOUND
    if reg.status != "pending":
        return jsonify({"error": "not_pending", "status": reg.status}), HTTPStatus.CONFLICT

    payload = request.get_json(silent=True) or {}
    reason = (payload.get("reason") or "").strip() or None

    reg.status = "rejected"
    if reason:
        reg.notes = (reg.notes or "") + f"\nREJECT_REASON: {reason}"
    reg.decided_by = getattr(getattr(request, "user", None), "id", None) or None

    db.session.commit()
    return jsonify({"ok": True}), HTTPStatus.OK
