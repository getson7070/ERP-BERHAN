# app.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_caching import Cache
from flask_babel import Babel
from flask_wtf import CSRFProtect

# --- core singletons (do NOT create Flask() here) ---
db = SQLAlchemy()
cache = Cache()
babel = Babel()
csrf = CSRFProtect()

# Socket.IO configured to use eventlet; CORS based on your env
socketio = SocketIO(
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "*"),
    async_mode="eventlet",  # critical for eventlet worker
    logger=False,
    engineio_logger=False,
)

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # ---- configuration ----
    # Flask secret keys – expects you to set FLASK_SECRET_KEY (or SECRET_KEY) in Render
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or "change-me"

    # Database URL – Render sets DATABASE_URL; your code sometimes also used sqlite
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # local/dev fallback (instance/erp.db)
        db_url = "sqlite:///" + os.path.join(app.instance_path, "erp.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Cache (simple default)
    app.config.setdefault("CACHE_TYPE", "SimpleCache")

    # ---- init extensions ----
    db.init_app(app)
    cache.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)

    # ---- blueprints / routes ----
    # These imports must be inside the factory to avoid premature app usage
    # Make sure the module names below match your project’s blueprint modules.
    #
    # from modules.dashboard.routes import bp as dashboard_bp
    # from modules.tenders.routes   import bp as tenders_bp
    # from modules.orders.routes    import bp as orders_bp
    # from modules.crm.routes       import bp as crm_bp
    # from modules.hr.routes        import bp as hr_bp
    # from modules.procurement.routes import bp as procurement_bp
    # from modules.manufacturing.routes import bp as manufacturing_bp
    # from modules.projects.routes  import bp as projects_bp
    # from modules.plugins.routes   import bp as plugins_bp
    #
    # app.register_blueprint(dashboard_bp)
    # app.register_blueprint(tenders_bp, url_prefix="/tenders")
    # app.register_blueprint(orders_bp, url_prefix="/orders")
    # app.register_blueprint(crm_bp, url_prefix="/crm")
    # app.register_blueprint(hr_bp, url_prefix="/hr")
    # app.register_blueprint(procurement_bp, url_prefix="/procurement")
    # app.register_blueprint(manufacturing_bp, url_prefix="/manufacturing")
    # app.register_blueprint(projects_bp, url_prefix="/projects")
    # app.register_blueprint(plugins_bp, url_prefix="/plugins")

    # Example root route (keep yours if you already have one)
    @app.route("/status")
    def status():
        return {"ok": True}

    return app
