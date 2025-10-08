import os
from flask import Flask, render_template
from flask_cors import CORS
from .extensions import init_extensions
from .routes.auth import auth_bp
from .routes.api import api_bp
from .routes.main import bp as main_bp  # public blueprint

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    # allow overriding via environment or instance config if you like
    app.config.from_mapping({})

    # CORS early
    CORS(app, supports_credentials=True)

    # init all extensions (db, migrate, cache, limiter, login, mail, socketio)
    init_extensions(app)

    # blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp,  url_prefix="/api")

    @app.get("/health")
    def health():
        return "ok", 200

    @app.get("/")
    def index():
        # entry template can be changed with ENTRY_TEMPLATE env/config
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    return app
