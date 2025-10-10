# erp/__init__.py
import os

# Must patch BEFORE importing anything that uses sockets/threads.
try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    pass  # allows running without eventlet locally

from flask import Flask, render_template, redirect, url_for, request
from .extensions import db, migrate, csrf, login_manager, limiter

# --- Config helpers ---
def _bool_env(name, default=False):
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1","true","yes","y","on")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-me")
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_ENABLED = True
    # using same secret unless explicitly set
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///berhan.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Limiter storage — optional Redis per requirement
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI")  # if None -> in-memory
    PREFERRED_URL_SCHEME = "https"

def create_app(config_object: type = Config):
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(config_object)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Limiter: choose redis if provided, else in-memory
    if app.config.get("RATELIMIT_STORAGE_URI"):
        limiter.storage_uri = app.config["RATELIMIT_STORAGE_URI"]
    limiter.init_app(app)

    # Login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models so user_loader can work
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Blueprints / routes
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Public pages (help/privacy/feedback) and 404 handling
    @app.get("/help")
    def help_page():
        return render_template("static_pages/help.html")

    @app.get("/privacy")
    def privacy_page():
        return render_template("static_pages/privacy.html")

    @app.route("/feedback", methods=["GET", "POST"])
    def feedback_page():
        if request.method == "POST":
            # TODO: persist or email feedback
            return render_template("static_pages/feedback_thanks.html")
        return render_template("static_pages/feedback.html")

    # Avoid raw 404s: send unknown routes to choose_login
    @app.errorhandler(404)
    def not_found(e):
        return redirect(url_for("main.choose_login"))

    # Health
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
