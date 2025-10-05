# erp/app.py
from __future__ import annotations

import os
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_cors import CORS

from .extensions import db, migrate, cache, limiter, login_manager, mail, socketio
from .models import User
from .web import web_bp
from .routes.auth import bp as auth_bp


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # ---- Config (env first, sensible fallbacks) ----
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///erp.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CORS_ORIGINS"] = os.getenv("CORS_ORIGINS", "*")
    app.config["RATELIMIT_STORAGE_URI"] = os.getenv("FLASK_LIMITER_STORAGE_URI", "memory://")
    app.config["CACHE_TYPE"] = os.getenv("CACHE_TYPE", "SimpleCache")
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # ---- Extensions ----
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config["CORS_ORIGINS"])
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        # Flask-Login: return user or None
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # ---- Blueprints ----
    app.register_blueprint(web_bp)     # “/”, /choose_login, /health
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # ---- Safety fallback routes ----
    @app.route("/index")
    def index():
        return redirect(url_for("web.choose_login"))

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
