import os
from flask import Flask, redirect, url_for
from flask_caching import Cache
from flask_compress import Compress
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_babel import Babel
from jinja2 import ChoiceLoader, FileSystemLoader
from erp import limiter, oauth
from db import ensure_schema

cache = Cache()
compress = Compress()
jwt = JWTManager()
babel = Babel()
socketio = SocketIO(async_mode="threading")  # no eventlet/gevent

def _register_blueprints(app: Flask):
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # ---- Config (safe defaults) ----
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(32)),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_TIME_LIMIT=None,
        CACHE_TYPE=os.environ.get("CACHE_TYPE", "SimpleCache"),
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", os.environ.get("SECRET_KEY", "change-me")),
        MFA_ISSUER=os.environ.get("MFA_ISSUER", "BERHAN ERP"),
        WEBAUTHN_RP_ID=os.environ.get("WEBAUTHN_RP_ID", "localhost"),
        WEBAUTHN_RP_NAME=os.environ.get("WEBAUTHN_RP_NAME", "BERHAN ERP"),
        WEBAUTHN_ORIGIN=os.environ.get("WEBAUTHN_ORIGIN"),  # optional
    )

    # ---- Extensions ----
    cache.init_app(app)
    compress.init_app(app)
    jwt.init_app(app)
    babel.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # OAuth client (SSO); keeps routes happy even if not used
    oauth.init_app(app)
    oauth.register(
        name="sso",
        client_id=os.environ.get("OAUTH_CLIENT_ID", "placeholder"),
        client_secret=os.environ.get("OAUTH_CLIENT_SECRET", "placeholder"),
        client_kwargs={"scope": "openid profile email"},
        authorize_url=os.environ.get("OAUTH_AUTHORIZE_URL", "https://example.com/authorize"),
        access_token_url=os.environ.get("OAUTH_TOKEN_URL", "https://example.com/token"),
        api_base_url=os.environ.get("OAUTH_BASE_URL", "https://example.com"),
    )
    app.config["OAUTH_USERINFO_URL"] = os.environ.get("OAUTH_USERINFO_URL", "https://example.com/userinfo")

    # ---- Jinja: search both locations ----
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(os.path.abspath("templates")),           # repo root
        FileSystemLoader(os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))),  # erp/templates
        app.jinja_loader,  # package defaults
    ])

    # ---- DB bootstrap (idempotent) ----
    ensure_schema()

    # ---- Routes ----
    @app.get("/")
    def index():
        return redirect(url_for("auth.choose_login"))

    _register_blueprints(app)
    return app
