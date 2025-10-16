from flask import Flask
from .config import Config
from .extensions import db
from .views.main import bp as main_bp

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    db.init_app(app)

    # Blueprints
    app.register_blueprint(main_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
