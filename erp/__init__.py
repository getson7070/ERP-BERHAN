from flask import Flask

def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__)
    if config_object:
        app.config.from_object(config_object)

    # --- extensions would be initialized here (db, cache, etc.) ---

    from .health import bp as health_bp
    app.register_blueprint(health_bp)

    return app