"""Client-facing authentication endpoints: registration, OTP verify, login, reset."""
from __future__ import annotations

from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Optional

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user

from erp.extensions import db
from erp.models import ClientAccount, ClientPasswordReset, ClientRoleAssignment, ClientVerification, Role
from erp.services.client_auth_utils import set_password, verify_password
from erp.utils import resolve_org_id

bp = Blueprint("client_auth_api", __name__, url_prefix="/api/client-auth")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _send_sms(phone: str, msg: str) -> None:  # pragma: no cover - integration placeholder
    # Wire this to your SMS provider (e.g., Twilio/local gateway)
    bp.logger.debug("SMS placeholder to %s: %s", phone, msg)


def _send_email(email: str, subject: str, msg: str) -> None:  # pragma: no cover - integration placeholder
    # Wire this to your email provider when available
    bp.logger.debug("Email placeholder to %s (%s): %s", email, subject, msg)


def _assign_role(account: ClientAccount, role_name: str) -> None:
    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()

    if not ClientRoleAssignment.query.filter_by(
        client_account_id=account.id, role_id=role.id
    ).first():
        db.session.add(ClientRoleAssignment(client_account_id=account.id, role_id=role.id))


def _revoke_sessions_for_account(account: ClientAccount) -> None:
    # Minimal session revocation: end current session if it belongs to this account.
    if current_user and getattr(current_user, "id", None) == account.id:
        logout_user()


# ---------------------------------------------------------------------------
# Registration + verification
# ---------------------------------------------------------------------------


@bp.post("/register")
def register_client():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    client_id = payload.get("client_id")
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    method = (payload.get("method") or "sms").lower()

    if not client_id:
        return jsonify({"error": "client_id required"}), HTTPStatus.BAD_REQUEST
    if not (phone or email):
        return jsonify({"error": "phone or email required"}), HTTPStatus.BAD_REQUEST
    if len(password) < 8:
        return jsonify({"error": "weak password"}), HTTPStatus.BAD_REQUEST

    if email and ClientAccount.query.filter_by(org_id=org_id, email=email).first():
        return jsonify({"error": "email already registered"}), HTTPStatus.CONFLICT
    if phone and ClientAccount.query.filter_by(org_id=org_id, phone=phone).first():
        return jsonify({"error": "phone already registered"}), HTTPStatus.CONFLICT

    account = ClientAccount(org_id=org_id, client_id=client_id, phone=phone or None, email=email or None)
    set_password(account, password)
    db.session.add(account)
    db.session.flush()

    code = ClientVerification.make_code()
    verification = ClientVerification(
        org_id=org_id,
        client_account_id=account.id,
        method=method,
        code_hash=ClientVerification.hash_code(code),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.session.add(verification)
    db.session.commit()

    if method == "sms" and phone:
        _send_sms(phone, f"Your verification code is {code}")
    elif method == "email" and email:
        _send_email(email, "Verify your account", f"Code: {code}")

    return jsonify({"account_id": account.id, "status": "otp_sent"}), HTTPStatus.CREATED


@bp.post("/verify")
def verify_client():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    account_id = payload.get("account_id")
    code = (payload.get("code") or "").strip()

    if not (account_id and code):
        return jsonify({"error": "account_id and code required"}), HTTPStatus.BAD_REQUEST

    account = ClientAccount.query.filter_by(org_id=org_id, id=account_id).first_or_404()
    if account.is_verified:
        return jsonify({"status": "already_verified"}), HTTPStatus.OK

    verification = (
        ClientVerification.query.filter_by(org_id=org_id, client_account_id=account.id, used_at=None)
        .order_by(ClientVerification.created_at.desc())
        .first()
    )
    if not verification or verification.is_expired():
        return jsonify({"error": "otp_expired"}), HTTPStatus.BAD_REQUEST
    if verification.code_hash != ClientVerification.hash_code(code):
        return jsonify({"error": "invalid_code"}), HTTPStatus.BAD_REQUEST

    verification.used_at = datetime.utcnow()
    account.is_verified = True
    account.verified_at = datetime.utcnow()
    _assign_role(account, "client")

    db.session.commit()
    return jsonify({"status": "verified"}), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Login / logout / profile
# ---------------------------------------------------------------------------


@bp.post("/login")
def client_login():
    """
    Client login endpoint with clearer outcomes for:
    - not registered (suggest registration)
    - inactive or awaiting approval
    - invalid password
    - successful login

    This does NOT perform redirects itself; the frontend should inspect the
    JSON payload and route the user to the appropriate screen.
    """
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    email = (payload.get("email") or "").strip().lower()
    phone = (payload.get("phone") or "").strip()
    password = payload.get("password") or ""

    account: Optional[ClientAccount] = None
    if email:
        account = ClientAccount.query.filter_by(org_id=org_id, email=email).first()
    if not account and phone:
        account = ClientAccount.query.filter_by(org_id=org_id, phone=phone).first()

    # 1) No account found at all – frontend should offer registration flow.
    if not account:
        return (
            jsonify(
                {
                    "error": "not_registered",
                    "need_registration": True,
                    "message": "No client account found for this email/phone.",
                }
            ),
            HTTPStatus.UNAUTHORIZED,
        )

    # 2) Account exists but is inactive (e.g. manually disabled).
    if not account.is_active:
        return (
            jsonify(
                {
                    "error": "inactive",
                    "approval_pending": False,
                    "need_support": True,
                    "message": "This client account is inactive. Please contact support.",
                }
            ),
            HTTPStatus.FORBIDDEN,
        )

    # 3) Account is active but not yet verified / fully approved.
    if not account.is_verified:
        return (
            jsonify(
                {
                    "error": "not_verified",
                    "approval_pending": True,
                    "message": "Your registration is received and pending approval.",
                }
            ),
            HTTPStatus.FORBIDDEN,
        )

    # 4) Password check
    if not verify_password(account, password):
        return (
            jsonify(
                {
                    "error": "invalid_password",
                    "message": "Incorrect password.",
                }
            ),
            HTTPStatus.UNAUTHORIZED,
        )

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

    return (
        jsonify(
            {
                "id": current_user.id,
                "client_id": getattr(current_user, "client_id", None),
                "email": getattr(current_user, "email", None),
                "phone": getattr(current_user, "phone", None),
                "is_verified": getattr(current_user, "is_verified", False),
            }
        ),
        HTTPStatus.OK,
    )


@bp.put("/me")
def update_profile():
    if not current_user or not getattr(current_user, "id", None):
        return jsonify({"error": "not_logged_in"}), HTTPStatus.UNAUTHORIZED

    payload = request.get_json(silent=True) or {}
    if "email" in payload:
        current_user.email = (payload.get("email") or "").strip().lower() or None
    if "phone" in payload:
        current_user.phone = (payload.get("phone") or "").strip() or None

    db.session.commit()
    return jsonify({"status": "updated"}), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


@bp.post("/password/forgot")
def forgot_password():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    email = (payload.get("email") or "").strip().lower()
    phone = (payload.get("phone") or "").strip()

    account: Optional[ClientAccount] = None
    if email:
        account = ClientAccount.query.filter_by(org_id=org_id, email=email).first()
    if not account and phone:
        account = ClientAccount.query.filter_by(org_id=org_id, phone=phone).first()

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
    set_password(account, new_password)

    reset.used_at = datetime.utcnow()
    _revoke_sessions_for_account(account)

    db.session.commit()
    return jsonify({"status": "password_updated"}), HTTPStatus.OK
