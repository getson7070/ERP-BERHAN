from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import (
    ClientAccount,
    ClientRegistration,
    ClientRoleAssignment,
    Institution,
    Role,
    User,
    UserMFA,
)
from erp.security_decorators_phase2 import require_permission
from erp.services.client_auth_utils import set_password
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


# --------------------------
# Employees/Admin users
# --------------------------

@bp.get("/users")
@require_permission("users", "view")
def list_users():
    org_id = resolve_org_id()
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([_serialize_user(u, org_id) for u in users]), HTTPStatus.OK


@bp.post("/users/<int:user_id>/roles/grant")
@require_permission("users", "manage_roles")
def grant_user_role(user_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role:
        return jsonify({"error": "role required"}), HTTPStatus.BAD_REQUEST

    try:
        grant_role_to_user(org_id=org_id, user_id=user_id, role_key=role, acting_user=current_user)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.FORBIDDEN
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return jsonify({"status": "granted", "role": role.lower()}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/roles/revoke")
@require_permission("users", "manage_roles")
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
@require_permission("users", "deactivate")
def deactivate_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    revoke_all_sessions_for_user(user_id, getattr(current_user, "id", None))
    db.session.commit()
    return jsonify({"status": "deactivated"}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/reactivate")
@require_permission("users", "reactivate")
def reactivate_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    return jsonify({"status": "reactivated"}), HTTPStatus.OK


@bp.post("/users/<int:user_id>/mfa/init")
@require_permission("users", "mfa_manage")
def init_mfa(user_id: int):
    user = User.query.get_or_404(user_id)
    secret = generate_totp_secret()
    uri = get_totp_uri(user.email or f"user{user.id}@erp", secret)
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
# C2: Client onboarding approvals
# --------------------------

def _ensure_role(role_name: str) -> Role:
    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()
    return role


def _grant_client_role(account: ClientAccount, role_name: str = "client") -> None:
    role = _ensure_role(role_name)
    exists = ClientRoleAssignment.query.filter_by(client_account_id=account.id, role_id=role.id).first()
    if not exists:
        db.session.add(ClientRoleAssignment(client_account_id=account.id, role_id=role.id))


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
                "uuid": r.public_id,
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
                "gps_hint": r.gps_hint,
                "notes": r.notes,
                "decided_by": r.decided_by,
                "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                "decision_notes": r.decision_notes,
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

    # 1) Create or fetch institution by TIN (unique per org)
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
            gps_hint=reg.gps_hint,
            main_phone=reg.phone,
            main_email=reg.email,
        )
        db.session.add(inst)
        db.session.flush()

    # 2) Create ClientAccount (email unique per org)
    existing = ClientAccount.query.filter_by(org_id=org_id, email=reg.email).first()
    if existing:
        return jsonify({"error": "client_account_email_exists"}), HTTPStatus.CONFLICT

    # ClientAccount.client_id is required in your model; we map it to Institution.id as the stable key.
    account = ClientAccount(
        org_id=org_id,
        client_id=inst.id,
        institution_id=inst.id,
        email=reg.email,
        phone=reg.phone,
        is_active=True,
        is_verified=True,
        verified_at=datetime.utcnow(),
    )
    # Preserve the password hash from registration
    account.password_hash = reg.password_hash
    db.session.add(account)
    db.session.flush()

    _grant_client_role(account, "client")

    # 3) Mark registration as approved
    reg.status = "approved"
    reg.decided_by = getattr(current_user, "id", None)
    reg.decided_at = datetime.utcnow()
    reg.decision_notes = (request.get_json(silent=True) or {}).get("decision_notes") or None

    db.session.commit()

    return (
        jsonify(
            {
                "ok": True,
                "institution_id": inst.id,
                "client_account_id": account.id,
            }
        ),
        HTTPStatus.OK,
    )


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
    notes = (payload.get("decision_notes") or "").strip() or None

    reg.status = "rejected"
    reg.decided_by = getattr(current_user, "id", None)
    reg.decided_at = datetime.utcnow()
    reg.decision_notes = notes

    db.session.commit()
    return jsonify({"ok": True}), HTTPStatus.OK
