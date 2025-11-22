"""OAuth scaffold for client accounts (Google-ready, with graceful degradation)."""
from __future__ import annotations

from http import HTTPStatus
from typing import Optional

from flask import Blueprint, jsonify, redirect, url_for, current_app

try:  # Optional dependency
    from authlib.integrations.flask_client import OAuth
except Exception:  # pragma: no cover - authlib not installed
    OAuth = None

from erp.extensions import db
from erp.models import ClientAccount, ClientOAuthAccount
from erp.utils import resolve_org_id

bp = Blueprint("client_oauth_api", __name__, url_prefix="/api/client-oauth")
oauth: Optional[OAuth] = OAuth() if OAuth else None


def init_oauth(app):  # pragma: no cover - configuration helper
    if not oauth:
        app.logger.warning("Authlib not installed; client OAuth disabled")
        return
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@bp.record_once
def _configure_oauth(state):  # pragma: no cover - ensures blueprint setup
    if oauth:
        init_oauth(state.app)


@bp.get("/google/login")
def google_login():
    if not oauth or "google" not in oauth._clients:  # type: ignore[attr-defined]
        return jsonify({"error": "oauth_unconfigured"}), HTTPStatus.NOT_IMPLEMENTED
    redirect_uri = url_for("client_oauth_api.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)  # type: ignore[union-attr]


@bp.get("/google/callback")
def google_callback():
    if not oauth or "google" not in oauth._clients:  # type: ignore[attr-defined]
        return jsonify({"error": "oauth_unconfigured"}), HTTPStatus.NOT_IMPLEMENTED

    org_id = resolve_org_id()
    token = oauth.google.authorize_access_token()  # type: ignore[union-attr]
    user_info = token.get("userinfo") or {}
    provider_user_id = user_info.get("sub")
    email = (user_info.get("email") or "").lower()

    if not provider_user_id:
        return jsonify({"error": "provider_error"}), HTTPStatus.BAD_REQUEST

    link = ClientOAuthAccount.query.filter_by(
        org_id=org_id, provider="google", provider_user_id=provider_user_id
    ).first()

    if link:
        account = ClientAccount.query.filter_by(org_id=org_id, id=link.client_account_id).first()
        if not account:
            return jsonify({"error": "account_missing"}), HTTPStatus.NOT_FOUND
        # login_user(account)  # If you wire flask-login for client sessions
        return redirect(current_app.config.get("CLIENT_PORTAL_URL", "/client-portal"))

    account = ClientAccount(org_id=org_id, client_id=0, email=email, is_verified=True)
    db.session.add(account)
    db.session.flush()

    db.session.add(
        ClientOAuthAccount(
            org_id=org_id,
            client_account_id=account.id,
            provider="google",
            provider_user_id=provider_user_id,
            provider_email=email,
        )
    )
    db.session.commit()

    # login_user(account)  # optional when client portal session is desired
    return redirect(current_app.config.get("CLIENT_PORTAL_URL", "/client-portal"))
