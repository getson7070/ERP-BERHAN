# --- inside create_app(), keep everything else as-is above this block ---

    _security_hardening(app)

    # Blueprints (use the names actually exported by the route modules)
    from .routes.auth import bp as auth_bp
    from .routes.dashboard_customize import bp as dashboard_bp  # this file already sets url_prefix="/dashboard"

    # Register WITHOUT adding another prefix to auth (some routes already contain "/auth/...")
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def index():
        # land users on the login chooser (exists in auth.py)
        return redirect(url_for("auth.choose_login"))

    @app.route("/login")
    def login_redirect():
        # convenience path if users or links point to /login
        return redirect(url_for("auth.choose_login"))

    return app
