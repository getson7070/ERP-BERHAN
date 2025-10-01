import os
from flask import Flask, jsonify

from erp.extensions import init_extensions

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # ---- Minimal, safe defaults (overridden by environment) ----
    # DB: you already set SQLALCHEMY_DATABASE_URI in Render env (postgresql+psycopg2://...).
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # CORS/cache defaults so you don't get noisy warnings
    app.config.setdefault("CORS_ORIGINS", "*")
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))  # avoids "CACHE_TYPE is null" warn

    # Rate limit storage (Limiter is constructed with storage_uri in extensions.py)
    app.config.setdefault("RATELIMIT_DEFAULT", "200/hour")

    # ---- Init shared extensions (db, migrate, oauth, cors, limiter, cache, jwt, socketio, etc.) ----
    init_extensions(app)

    # ---- Explicitly register your actual blueprints (these exist in your repo) ----
    # NOTE: Your earlier auto-register tried "erp.auth" (doesn't exist). The real modules live in erp.routes.*
    from erp.routes.auth import bp as auth_bp      # /login, /choose-login
    from erp.routes.main import bp as main_bp      # /dashboard
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # ---- Health endpoint (Render health checks) ----
    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    # DO NOT register "/" here to avoid collisions/loops.
    # Let main blueprint own app landing (you currently serve /dashboard there).
    # Your external links or UI should go to /login (unauth) or /dashboard (auth).

    return app
