# erp/app.py
import os
from flask import Flask, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_socketio import SocketIO
from .extensions import db, limiter, oauth, jwt, cache, compress, csrf, babel

socketio = SocketIO(
    async_mode="eventlet",
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "*"),
    message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"),  # set to redis://... when scaling
)

def _security_hardening(app: Flask) -> None:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PREFERRED_URL_SCHEME="https",
        WTF_CSRF_TIME_LIMIT=None,
    )
    @app.after_request
    def _headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "geolocation=()")
        return resp

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Secrets / DB
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("FLASK_SECRET_KEY/SECRET_KEY not set")

    os.makedirs(app.instance_path, exist_ok=True)
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'erp.db')}"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # JWT / Cache / Rate limiting
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", app.config["SECRET_KEY"])
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("RATELIMIT_ENABLED", True)
    # Prefer explicit RATELIMIT_STORAGE_URI; else reuse Redis if provided
    ratelimit_uri = os.getenv("RATELIMIT_STORAGE_URI") or os.getenv("REDIS_URL") or "memory://"
    app.config["RATELIMIT_STORAGE_URI"] = ratelimit_uri
    app.config.setdefault("RATELIMIT_DEFAULT", os.getenv("DEFAULT_RATE_LIMITS", "60 per minute"))

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # OAuth (routes import oauth even if you don’t configure providers; that’s fine)
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    token_url = os.getenv("OAUTH_TOKEN_URL")
    auth_url = os.getenv("OAUTH_AUTH_URL")
    userinfo_url = os.getenv("OAUTH_USERINFO_URL")
    if client_id and client_secret and auth_url and token_url:
        oauth.init_app(app)
        oauth.register(
            name="sso",
            client_id=client_id,
            client_secret=client_secret,
            access_token_url=token_url,
            authorize_url=auth_url,
            api_base_url=os.getenv("OAUTH_API_BASE", ""),
            client_kwargs={"scope": "openid profile email"},
        )
        app.config.setdefault("OAUTH_USERINFO_URL", userinfo_url or "")

    _security_hardening(app)

    # Blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard_customize import dashboard_bp  # change if your main BP differs
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app
