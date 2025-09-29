# wsgi.py
import os

# Your app factory lives in your project package. In your logs the logger name is "erp",
# so we try that first and fall back to a generic "app" package if needed.
try:
    from erp import create_app  # preferred (matches your logger name)
except ImportError:  # fallback, in case the package is named "app"
    from app import create_app

# Render sets FLASK_ENV via your Dashboard. Use it if present; default to "production".
flask_env = os.environ.get("FLASK_ENV", "production")

# Some codebases define create_app() with no parameters; others accept an env string.
# Call compatibly so we don’t crash at import time.
try:
    app = create_app(flask_env)  # try passing env
except TypeError:
    app = create_app()  # factory that takes no args

# Ensure there is a lightweight health endpoint for Render’s health checks.
# (Won’t override if you already have one wired up.)
if not any(r.rule == "/healthz" for r in getattr(app, "url_map", []).iter_rules()):
    @app.route("/healthz", methods=["GET"])
    def _healthz():
        return "ok", 200
