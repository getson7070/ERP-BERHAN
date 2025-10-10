import os
from flask import Flask, render_template, request, jsonify
from erp.extensions import db, login_manager

def create_app(config_object=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Load config
    app.config.from_object(config_object or os.getenv("FLASK_CONFIG", "erp.config.ProductionConfig"))
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "change-me"))  # ensure sessions work

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # --- Auth wiring: user loader(s) ---
    # Import here to avoid circulars
    from erp.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        """
        Return a User by primary key for session-based auth.
        Use SQLAlchemy 2.0-safe 'db.session.get'.
        Guarded so deploys don't 500 if migrations haven't run yet.
        """
        try:
            # User IDs are ints; return None on bad casts or DB errors.
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    @login_manager.request_loader
    def load_user_from_request(req: "request"):
        """
        Optional token-based hook. Return None to skip silently.
        This prevents Flask-Login from raising during template context updates.
        """
        _ = req.headers.get("Authorization") or req.headers.get("X-Auth-Token")
        return None

    # --- Blueprints (adjust if your modules differ) ---
    try:
        from erp.auth.routes import bp as auth_bp
        app.register_blueprint(auth_bp)
    except Exception:
        pass

    try:
        from erp.main.routes import bp as main_bp
        app.register_blueprint(main_bp)
    except Exception:
        pass

    # --- Health check: fast, no DB, no auth, always 200 ---
    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok"), 200

    # --- Error handlers ---
    @app.errorhandler(500)
    def server_error(e):
        # Template is fine; with loaders above, current_user resolves safely
        return render_template("errors/500.html"), 500

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app
