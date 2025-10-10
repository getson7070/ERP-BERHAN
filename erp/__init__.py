# erp/__init__.py
from flask import Flask
from .extensions import csrf
from .routes.main import main_bp
from .routes.auth import auth_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # --- Minimal required config (keep your existing SECRET_KEY etc.) ---
    # Make sure SECRET_KEY is set via env in production
    app.config.setdefault("SECRET_KEY", "change-me-in-prod")

    # --- CSRF: enable + inject helper for Jinja ---
    csrf.init_app(app)

    @app.context_processor
    def inject_csrf():
        # allows {{ csrf_token() }} in templates
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # --- Blueprints ---
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app
