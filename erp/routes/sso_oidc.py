from __future__ import annotations

import importlib.util
from http import HTTPStatus

from flask import Blueprint, current_app, jsonify, redirect, url_for

from erp.extensions import db
from erp.models import User
from erp.services.role_service import grant_role_to_user
from erp.utils import resolve_org_id

oauth = None
# authlib is optional; only wire OIDC if the base package is present
if importlib.util.find_spec("authlib"):
    from authlib.integrations.flask_client import OAuth

    oauth = OAuth()

bp = Blueprint("sso_oidc", __name__, url_prefix="/api/sso")


def init_sso(app):
    if oauth is None:
        return
    oauth.init_app(app)
    oauth.register(
        name="oidc",
        client_id=app.config.get("OIDC_CLIENT_ID"),
        client_secret=app.config.get("OIDC_CLIENT_SECRET"),
        server_metadata_url=app.config.get("OIDC_METADATA_URL"),
        client_kwargs={"scope": "openid email profile"},
    )


@bp.get("/login")
def sso_login():
    if oauth is None or "oidc" not in oauth.apps:
        return jsonify({"error": "oidc_not_configured"}), HTTPStatus.SERVICE_UNAVAILABLE
    redirect_uri = url_for("sso_oidc.sso_callback", _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)


@bp.get("/callback")
def sso_callback():
    if oauth is None or "oidc" not in oauth.apps:
        return jsonify({"error": "oidc_not_configured"}), HTTPStatus.SERVICE_UNAVAILABLE

    org_id = resolve_org_id()
    token = oauth.oidc.authorize_access_token()
    info = token.get("userinfo") or {}

    email = (info.get("email") or "").lower()
    full_name = info.get("name") or email

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(
            username=email.split("@", 1)[0],
            email=email,
            full_name=full_name,
            org_id=resolve_org_id(),
        )
        db.session.add(user)
        db.session.flush()
        grant_role_to_user(org_id=org_id, user_id=user.id, role_key="employee", acting_user=None)
    elif not getattr(user, "full_name", None):
        user.full_name = full_name

    db.session.commit()
    return redirect(current_app.config.get("SSO_SUCCESS_REDIRECT", "/"))
