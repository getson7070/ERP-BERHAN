import os
from flask import Flask, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO

# --- singletons (imported by blueprints) ---
db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()

# Socket.IO with Redis message queue (works even without a Redis URL)
socketio = SocketIO(
    async_mode="eventlet",
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "*"),
    message_queue=os.getenv("CELERY_BROKER_URL")  # reuse Redis if you have it
)

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # ---- Core configuration ----
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instance/erp.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", app.config["SECRET_KEY"])
    app.config["SECURITY_PASSWORD_SALT"] = os.getenv("SECURITY_PASSWORD_SALT", "change-me")
    app.config["PREFERRED_URL_SCHEME"] = "https"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    # Caching (simple by default)
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 300)

    # ---- Init extensions ----
    CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    socketio.init_app(app)

    # ---- Blueprints ----
    # Import/register your existing blueprints here.
    # Example:
    # from erp.web.views import web_bp
    # app.register_blueprint(web_bp)
    #
    # Repeat for: tenders_bp, orders_bp, crm_bp, hr_bp, procurement_bp, manufacturing_bp, projects_bp, plugins_bp, etc.

    # ---- Default route: send to login, not dashboard ----
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))  # ensure your auth blueprint is named 'auth'

    # ---- Error pages ----
    @app.errorhandler(500)
    def _500(e):
        # Keep your existing template name if different
        return ("""
            <!doctype html><title>Error</title>
            <h1>Something went wrong</h1>
            <p>We’ve logged the error. Try again or contact support.</p>
        """, 500)

    return app
