"""Client-facing authentication endpoints (API): registration request, login, reset.

This API is aligned with the system's intended client onboarding model:
- Anonymous clients submit a registration request (TIN + institution + contact + address).
- Registration is pending until approved by management/admin.
- Upon approval, the system creates an Institution (TIN unique) and a ClientAccount.
- ClientAccount.is_verified is the session gate (enforced by Flask-Login loader).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Optional

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash

from erp.extensions import db
from erp.models import ClientAccount, ClientPasswordReset, ClientRegistration
from erp.services.client_auth_utils import verify_password
from erp.utils import resolve_org_id

bp = Blueprint("client_auth_api", __name__, url_prefix="/api/client-auth")


def _norm_email(v: str | None) -> str:
    return (v or "").strip().lower()


def _norm(v: str | None) -> str:
    return (v or "").strip()


def _valid_tin(tin: str) -> bool:
    # Ethiopia: 10-digit, typically starting with 0; your DB constraints enforce 10 digits.
    return bool(re.fullmatch(r"\d{10}", tin))


@bp.get("/registration/status")
def registration_status():
    """Check registration status by (tin + email).

    Query params:
      - tin (required)
      - email (required)
    """
    org_id = resolve_org_id()
    tin = _norm(request.args.get("tin"))
    email = _norm_email(request.args.get("email"))

    if not _valid_tin(tin):
        return jsonify({"error": "invalid_tin"}), HTTPStatus.BAD_REQUEST
    if not email:
        return jsonify({"error": "email_required"}), HTTPStatus.BAD_REQUEST

    reg = ClientRegistration.query.filter_by(org_id=org_id, tin=tin, email=email).first()
    if not reg:
        return jsonify({"status": "not_found"}), HTTPStatus.OK

    return (
        jsonify(
            {
                "status": reg.status,
                "registration_id": reg.public_id,
                "decided_at": reg.decided_at.isoformat() if reg.decided_at else None,
                "decision_notes": reg.decision_notes,
            }
        ),
        HTTPStatus.OK,
    )


@bp.post("/register")
def register_client():
    """Submit a client registration request (approval-gated).

    Required:
      - tin (10 digits)
      - institution_name
      - email
      - contact_name
      - password (>= 8)
    Optional:
      - phone, contact_position, institution_type
      - region, zone, city, subcity, woreda, kebele, street, house_number, gps_hint, notes
    """
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    tin = _norm(payload.get("tin"))
    institution_name = _norm(payload.get("institution_name"))
    institution_type = _norm(payload.get("institution_type")) or None

    contact_name = _norm(payload.get("contact_name"))
    contact_position = _norm(payload.get("contact_position")) or None

    email = _norm_email(payload.get("email"))
    phone = _norm(payload.get("phone")) or None

    region = _norm(payload.get("region")) or None
    zone = _norm(payload.get("zone")) or None
    city = _norm(payload.get("city")) or None
    subcity = _norm(payload.get("subcity")) or None
    woreda = _norm(payload.get("woreda")) or None
    kebele = _norm(payload.get("kebele")) or None
    street = _norm(payload.get("street")) or None
    house_number = _norm(payload.get("house_number")) or None
    gps_hint = _norm(payload.get("gps_hint")) or None
    notes = _norm(payload.get("notes")) or None

    password = payload.get("password") or ""
    if not _valid_tin(tin):
        return jsonify({"error": "invalid_tin"}), HTTPStatus.BAD_REQUEST
    if not institution_name:
        return jsonify({"error": "institution_name_required"}), HTTPStatus.BAD_REQUEST
    if not contact_name:
        return jsonify({"error": "contact_name_required"}), HTTPStatus.BAD_REQUEST
    if not email:
        return jsonify({"error": "email_required"}), HTTPStatus.BAD_REQUEST
    if len(password) < 8:
        return jsonify({"error": "weak_password"}), HTTPStatus.BAD_REQUEST

    # If account already exists, registration is not allowed.
    existing_account = ClientAccount.query.filter_by(org_id=org_id, email=email).first()
    if existing_account:
        return (
            jsonify(
                {
                    "error": "account_exists",
                    "message": "An account with this email already exists. Please login or reset password.",
                }
            ),
            HTTPStatus.CONFLICT,
        )

    # If same tin+email registration exists:
    existing_reg = ClientRegistration.query.filter_by(org_id=org_id, tin=tin, email=email).first()
    if existing_reg:
        return (
            jsonify(
                {
                    "status": existing_reg.status,
                    "registration_id": existing_reg.public_id,
                    "message": "A registration for this contact already exists.",
                }
            ),
            HTTPStatus.OK,
        )

    reg = ClientRegistration(
        org_id=org_id,
        tin=tin,
        institution_name=institution_name,
        institution_type=institution_type,
        contact_name=contact_name,
        contact_position=contact_position,
        email=email,
        phone=phone,
        region=region,
        zone=zone,
        city=city,
        subcity=subcity,
        woreda=woreda,
        kebele=kebele,
        street=street,
        house_number=house_number,
        gps_hint=gps_hint,
        notes=notes,
        password_hash=generate_password_hash(password),
        status="pending",
    )
    db.session.add(reg)
    db.session.commit()

    return (
        jsonify(
            {
                "status": "pending",
                "registration_id": reg.public_id,
                "message": "Registration submitted. Awaiting management approval.",
            }
        ),
        HTTPStatus.CREATED,
    )


@bp.post("/login")
def client_login():
    """Client login (approval-gated).

    Returns clear outcomes for:
      - not registered
      - pending approval
      - rejected
      - inactive
      - invalid password
      - success
    """
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    email = _norm_email(payload.get("email"))
    phone = _norm(payload.get("phone"))
    password = (payload.get("password") or "").strip()

    if not (email or phone):
        return jsonify({"error": "missing_identifier"}), HTTPStatus.BAD_REQUEST
    if not password:
        return jsonify({"error": "missing_password"}), HTTPStatus.BAD_REQUEST

    account: Optional[ClientAccount] = None
    if email:
        account = ClientAccount.query.filter_by(org_id=org_id, email=email).first()
    if not account and phone:
        account = ClientAccount.query.filter_by(org_id=org_id, phone=phone).first()

    # If no account, check for pending/decided registration and return guidance.
    if not account:
        # Best-effort: if email provided, search latest registration by email.
        reg = None
        if email:
            reg = (
                ClientRegistration.query.filter_by(org_id=org_id, email=email)
                .order_by(ClientRegistration.id.desc())
                .first()
            )
        if reg:
            if reg.status == "pending":
                return (
                    jsonify(
                        {
                            "error": "approval_pending",
                            "need_registration": False,
                            "message": "Your registration is pending approval.",
                        }
                    ),
                    HTTPStatus.FORBIDDEN,
                )
            if reg.status == "rejected":
                return (
                    jsonify(
                        {
                            "error": "rejected",
                            "need_support": True,
                            "message": "Your registration was rejected. Please contact support.",
                        }
                    ),
                    HTTPStatus.FORBIDDEN,
                )
            # approved registration but no account indicates admin process incomplete.
            if reg.status == "approved":
                return (
                    jsonify(
                        {
                            "error": "approved_but_no_account",
                            "need_support": True,
                            "message": "Registration approved but account not provisioned. Please contact support.",
                        }
                    ),
                    HTTPStatus.CONFLICT,
                )

        return (
            jsonify(
                {
                    "error": "not_registered",
                    "need_registration": True,
                    "message": "No client account found. Please register.",
                }
            ),
            HTTPStatus.UNAUTHORIZED,
        )

    if not account.is_active:
        return (
            jsonify(
                {
                    "error": "inactive",
                    "need_support": True,
                    "message": "This account is inactive. Please contact support.",
                }
            ),
            HTTPStatus.FORBIDDEN,
        )

    if not getattr(account, "is_verified", False):
        return (
            jsonify(
                {
                    "error": "not_approved",
                    "approval_pending": True,
                    "message": "Your account is not yet approved.",
                }
            ),
            HTTPStatus.FORBIDDEN,
        )

    if not verify_password(account, password):
        return jsonify({"error": "invalid_password"}), HTTPStatus.UNAUTHORIZED

    login_user(account)
    account.last_login_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"status": "ok"}), HTTPStatus.OK


@bp.post("/logout")
def client_logout():
    logout_user()
    return jsonify({"status": "ok"}), HTTPStatus.OK


@bp.get("/me")
def client_me():
    if not current_user or not getattr(current_user, "id", None):
        return jsonify({"error": "not_logged_in"}), HTTPStatus.UNAUTHORIZED

    # current_user may be employee or client depending on session
    return (
        jsonify(
            {
                "id": getattr(current_user, "id", None),
                "email": getattr(current_user, "email", None),
                "phone": getattr(current_user, "phone", None),
                "is_client": str(getattr(current_user, "get_id", lambda: "")()).startswith("client:"),
            }
        ),
        HTTPStatus.OK,
    )


# ---------------------------------------------------------------------------
# Password reset (client accounts only)
# ---------------------------------------------------------------------------

def _send_sms(phone: str, msg: str) -> None:  # pragma: no cover
    bp.logger.debug("SMS placeholder to %s: %s", phone, msg)


def _send_email(email: str, subject: str, msg: str) -> None:  # pragma: no cover
    bp.logger.debug("Email placeholder to %s (%s): %s", email, subject, msg)


@bp.post("/password/forgot")
def forgot_password():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    phone = _norm(payload.get("phone"))

    account: Optional[ClientAccount] = None
    if email:
        account = ClientAccount.query.filter_by(org_id=org_id, email=email).first()
    if not account and phone:
        account = ClientAccount.query.filter_by(org_id=org_id, phone=phone).first()

    # Do not reveal existence.
    if not account or not account.is_active:
        return jsonify({"status": "if_exists_sent"}), HTTPStatus.OK

    token = ClientPasswordReset.make_token()
    reset = ClientPasswordReset(
        org_id=org_id,
        client_account_id=account.id,
        token_hash=ClientPasswordReset.hash_token(token),
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.session.add(reset)
    db.session.commit()

    if account.email:
        _send_email(account.email, "Password Reset", f"Reset token: {token}")
    if account.phone:
        _send_sms(account.phone, f"Reset token: {token}")

    return jsonify({"status": "if_exists_sent"}), HTTPStatus.OK


@bp.post("/password/reset")
def reset_password():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    token = (payload.get("token") or "").strip()
    new_password = payload.get("new_password") or ""

    if len(new_password) < 8:
        return jsonify({"error": "weak_password"}), HTTPStatus.BAD_REQUEST

    reset = ClientPasswordReset.query.filter_by(
        org_id=org_id,
        token_hash=ClientPasswordReset.hash_token(token),
        used_at=None,
    ).first()

    if not reset or reset.is_expired():
        return jsonify({"error": "invalid_or_expired"}), HTTPStatus.BAD_REQUEST

    account = ClientAccount.query.filter_by(org_id=org_id, id=reset.client_account_id).first_or_404()
    account.password_hash = generate_password_hash(new_password)

    reset.used_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "password_updated"}), HTTPStatus.OK
