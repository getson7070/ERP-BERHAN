# erp/app.py
import os
from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS
from .extensions import init_extensions, limiter, db
from .routes.main import bp as main_bp
from .routes.auth import auth_bp

def _bootstrap_admin(app: Flask) -> None:
    """Create a default admin once, if ADMIN_EMAIL/PASSWORD env vars provided."""
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return
    from .models import User
    with app.app_context():
        if not db.session.query(User).filter_by(email=admin_email).first():
            u = User(email=admin_email, role="admin")
            u.set_password(admin_password)
            db.session.add(u)
            db.session.commit()
            app.logger.info("Seeded default admin: %s", admin_email)

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev"))
    app.config.setdefault("ENTRY_TEMPLATE", os.getenv("ENTRY_TEMPLATE", "choose_login.html"))

    # CORS
    CORS(app, supports_credentials=True)

    # Extensions
    init_extensions(app)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Index
    @app.route("/")
    def index():
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    # Health (no rate limit)
    @app.get("/health")
    def health():
        return "ok", 200
    limiter.exempt(health)

    # Optional: redirect /home to dashboard
    @app.get("/home")
    def home():
        return redirect(url_for("main.dashboard"))

    # Seed default admin
    _bootstrap_admin(app)

    return app
