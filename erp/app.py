import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()

socketio = SocketIO(
    async_mode="eventlet",
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "*"),
    message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"),
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

def _limiter() -> Limiter:
    return Limiter(
        key_func=get_remote_address,
        default_limits=os.getenv("DEFAULT_RATE_LIMITS", "60/minute"),
        storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        enabled=os.getenv("RATELIMIT_ENABLED", "1") == "1",
    )

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("FLASK_SECRET_KEY/SECRET_KEY not set")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'erp.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", app.config["SECRET_KEY"])
    app.config["CACHE_TYPE"] = "SimpleCache"

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    _limiter().init_app(app)
    babel.init_app(app)
    socketio.init_app(app)

    _security_hardening(app)

    from erp.routes.auth import auth_bp
    from erp.routes.dashboard_customize import dashboard_bp  # adjust to your main blueprint

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app
