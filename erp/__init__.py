from __future__ import annotations

import os
from flask import Flask
from .extensions import db, migrate, login_manager, csrf, socketio, limiter
from .routes.auth import auth_bp
from .routes.inventory import inventory_bp
from .routes.orders import orders_bp
from .routes.marketing import marketing_bp

DEFAULT_SECRET = "change-me-please"

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Core config
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", DEFAULT_SECRET),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL", "sqlite:///erp.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    # ---- Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode=os.getenv("SOCKETIO_ASYNC_MODE", "eventlet"))

    # Rate limiting
    limiter.init_app(app)


    # ---- Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(marketing_bp, url_prefix="/marketing")

    # ---- Health route
    @app.get("/healthz")
    def health():
        return {"status": "ok", "time": "2025-10-15 08:42:15"}, 200

    

# ---- Security headers
@app.after_request
def set_security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return resp

return app
