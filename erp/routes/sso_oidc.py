"""SSO OIDC route – gracefully handles missing Authlib (optional dependency)."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, current_app, jsonify

bp = Blueprint("sso_oidc", __name__, url_prefix="/api/sso")

# Global flag — set during app init
_oidc_available = False

def init_sso(app):
    """Called from create_app() — safe even if authlib is not installed."""
    global _oidc_available
    try:
        from authlib.integrations.flask_client import OAuth
        oauth = OAuth(app)
        oauth.register(
            name="oidc",
            client_id=app.config.get("OIDC_CLIENT_ID"),
            client_secret=app.config.get("OIDC_CLIENT_SECRET"),
            server_metadata_url=app.config.get("OIDC_METADATA_URL"),
            client_kwargs={"scope": "openid email profile"},
        )
        app.extensions["sso_oauth"] = oauth
        _oidc_available = True
        app.logger.info("SSO/OIDC enabled (authlib detected)")
    except Exception as e:  # authlib not installed or config missing
        _oidc_available = False
        app.logger.warning(f"SSO/OIDC disabled: {e}")


@bp.get("/login")
def sso_login():
    if not _oidc_available:
        return jsonify({"error": "SSO/OIDC not configured or authlib missing"}), HTTPStatus.SERVICE_UNAVAILABLE
    oauth = current_app.extensions["sso_oauth"]
    redirect_uri = current_app.config.get("SSO_REDIRECT_URI") or "/api/sso/callback"
    return oauth.oidc.authorize_redirect(redirect_uri)


@bp.get("/callback")
def sso_callback():
    if not _oidc_available:
        return jsonify({"error": "SSO/OIDC not configured"}), HTTPStatus.SERVICE_UNAVAILABLE

    from erp.extensions import db
    from erp.models import User
    from erp.services.role_service import grant_role_to_user
    from erp.utils import resolve_org_id

    oauth = current_app.extensions["sso_oauth"]
    token = oauth.oidc.authorize_access_token()
    userinfo = token.get("userinfo") or oauth.oidc.parse_id_token(token)

    email = (userinfo.get("email") or "").lower()
    if not email:
        return jsonify({"error": "No email in OIDC response"}), HTTPStatus.BAD_REQUEST

    org_id = resolve_org_id()
    user = User.query.filter_by(email=email).first()
    if not user:
        username = email.split("@", 1)[0]
        user = User(
            username=username,
            email=email,
            full_name=userinfo.get("name") or username,
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()
        grant_role_to_user(org_id=org_id, user_id=user.id, role_key="employee", acting_user=None)
    else:
        if not user.full_name:
            user.full_name = userinfo.get("name") or user.full_name

    db.session.commit()

    redirect_to = current_app.config.get("SSO_SUCCESS_REDIRECT", "/")
    return redirect(redirect_to)