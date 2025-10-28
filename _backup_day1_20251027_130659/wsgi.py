# --- BEGIN minimal WSGI shim (safe to keep) ---

import os

# Only define these if the project didn't already provide them
if "create_app" not in globals():
    from flask import Flask

    def create_app():
        app = Flask(__name__)
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-not-secure")

        # Auto-register any Flask Blueprints under erp.blueprints.*
        try:
            import pkgutil, importlib, types
            from flask import Blueprint
            import erp.blueprints as _bp_pkg

            for _finder, _modname, _ispkg in pkgutil.walk_packages(
                _bp_pkg.__path__, _bp_pkg.__name__ + "."
            ):
                m = importlib.import_module(_modname)
                # register any Blueprint objects defined in the module
                for name, val in vars(m).items():
                    if isinstance(val, Blueprint):
                        app.register_blueprint(val)
        except Exception:
            # It's okay if no blueprints or package isn't present yet
            pass

        # Health endpoint (honors the compat flag you had in app.py)
        if os.getenv("ERP_ENABLE_HEALTH_COMPAT", "1") == "1":
            @app.get("/health/ready")
            def _ready():
                return "ok", 200

        return app

if "app" not in globals():
    app = create_app()

# Optional: expose a Celery instance for "celery -A erp.app.celery ..."
try:
    if "celery" not in globals():
        from celery import Celery

        def make_celery(flask_app):
            c = Celery(
                flask_app.import_name,
                broker=os.getenv("CELERY_BROKER_URL", "redis://cache:6379/0"),
                backend=os.getenv("CELERY_RESULT_BACKEND", "redis://cache:6379/1"),
            )
            c.conf.update(flask_app.config)

            TaskBase = c.Task
            class ContextTask(TaskBase):
                def __call__(self, *args, **kwargs):
                    with flask_app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)
            c.Task = ContextTask
            return c

        celery = make_celery(app)
except Exception:
    # If Celery isn't installed/needed in this env, that's fine.
    pass

# --- END minimal WSGI shim ---

# --- added by script: /health alias middleware ---
class HealthAliasMiddleware:
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        if environ.get("REQUEST_METHOD") == "GET" and environ.get("PATH_INFO") == "/health":
            start_response("200 OK", [("Content-Type","text/plain")])
            return [b"ok"]
        return self.app(environ, start_response)

app = HealthAliasMiddleware(app)
# --- end /health alias middleware ---
