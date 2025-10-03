# erp/app.py
import os
# ... the rest of your imports above

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    # ----- Add this block early (before init_extensions/app.register_blueprint) -----
    db_url = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "Provide SQLALCHEMY_DATABASE_URI or DATABASE_URL in the environment."
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    # -------------------------------------------------------------------------------

    # continue with the rest of your existing setup
    # init_extensions(app)
    # register blueprints, etc.
    return app
