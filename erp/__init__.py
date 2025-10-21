from flask import Flask
from .routes.health import bp as health_bp
from .routes.metrics import bp as metrics_bp
from .routes.analytics import bp as analytics_bp
from .api.webhook import bp as webhook_bp

def create_app(config_object=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.setdefault("SECRET_KEY", "dev-secret")
    app.config.setdefault("TESTING", True)

    if config_object:
        app.config.from_object(config_object)

    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(webhook_bp)

    @app.get("/help")
    def help_page():
        return "OK", 200

    @app.get("/offline")
    def offline_page():
        from flask import render_template
        return render_template("base.html")

    return app
