from .analytics import analytics_bp


def register_blueprints(app):
    app.register_blueprint(analytics_bp)
