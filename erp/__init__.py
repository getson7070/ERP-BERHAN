# erp/__init__.py  (within create_app)

from flask import request
from sqlalchemy import text
from .extensions import db
from .security.device import read_device_id, compute_activation_for_device

def create_app(config_object=None):
    app = Flask(__name__)
    # ... your existing init (config, db.init_app, login_manager, blueprints, etc.)

    @app.context_processor
    def inject_login_activation():
        """Exposes `login_activation` and `current_device_id` to all templates."""
        device_id = read_device_id(request)
        # Use a real DB connection bound to SQLAlchemy (no session state changes)
        bind = db.engine.connect()
        try:
            activation = compute_activation_for_device(bind, device_id)
        finally:
            bind.close()

        # You can also drop a cookie if you want to persist the device id later.
        return {
            "login_activation": activation,       # dict: {'client': True, 'employee': False, 'admin': False}
            "current_device_id": device_id or "", # for debugging / help page
        }

    return app
