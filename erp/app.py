# erp/app.py
import os
from flask import Flask, render_template
from .extensions import init_extensions
from flask_cors import CORS

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # --- Core config ---
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config.setdefault("TEMPLATES_AUTO_RELOAD", True)

    # CORS for local frontend or anything else:
    CORS(app, resources={r"*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

    # --- Extensions ---
    init_extensions(app)

    # --- Blueprints ---
    # Auth routes
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Main/web routes (your file is routes/main.py and exposes bp)
    try:
        from .routes.main import bp as web_bp
        app.register_blueprint(web_bp)
    except Exception as e:
        app.logger.warning("Main routes not registered: %s", e)

    # --- Home ---
    @app.route("/", methods=["GET"])
    def index():
        # point to a presentable entry page (see template below)
        return render_template("choose_login.html")

    # Simple health endpoint for Render
    @app.route("/health")
    def health():
        return "ok", 200

    return app
