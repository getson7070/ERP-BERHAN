import os
from flask import Flask
from flask_cors import CORS
from .extensions import db, migrate, csrf, login_manager, cache, mail, socketio, init_limiter
from .routes import register_blueprints
from .context import register_context_processors

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    # Config
    app.config.from_object("config.Config")

    # Core extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})
    mail.init_app(app)
    limiter = init_limiter(app)
    CORS(app, supports_credentials=True)

    # Login
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            from .models import User  # adjust to your actual models
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    register_context_processors(app)
    register_blueprints(app)  # safe autoregister

    # Basic health route if none exists
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app
