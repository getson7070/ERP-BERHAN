import os
from importlib import import_module
from typing import Iterable, Optional

from flask import Flask, jsonify, redirect, url_for, request

from .extensions import init_extensions, db, socketio


def _maybe_register_blueprint(app: Flask, module_name: str, candidates: Iterable[str], url_prefix: Optional[str] = None) -> None:
    """
    Tries to import `module_name` and register the first attribute that looks like a Blueprint.
    `candidates` is a list of attribute names to try (e.g. ["bp", "blueprint", "auth_bp"]).
    Silently skips if module or attribute is not present. This keeps the app robust when some
    feature modules are optional.
    """
    try:
        module = import_module(module_name)
    except Exception:
        return

    for attr in candidates:
        bp = getattr(module, attr, None)
        if bp is not None:
            try:
                app.register_blueprint(bp, url_prefix=url_prefix)
            except Exception:
                # If importing/registration errors occur, don't crash the whole app
                pass
            return


def create_app() -> Flask:
    from dotenv import load_dotenv

    load_dotenv()

    app = Flask(__name__)

    # --- Minimal, safe configuration defaults ---
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    # DB
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI") or "sqlite:///erp.db",
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # JWT
    app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "dev-jwt-secret"))

    # CORS
    app.config.setdefault("CORS_ORIGINS", os.getenv("CORS_ORIGINS", "*"))

    # Socket.IO queue (optional)
    app.config.setdefault("SOCKETIO_MESSAGE_QUEUE", os.getenv("REDIS_URL"))

    # Init all extensions (DB, Migrate, OAuth, CORS, Limiter, Cache, Compress, CSRF, Babel, JWT, SocketIO)
    init_extensions(app)

    # --- Blueprint registration (best-effort) ---
    # Try common auth locations/names; adjust to your project if needed.
    _maybe_register_blueprint(app, "erp.auth", ["bp", "blueprint", "auth_bp", "auth"], url_prefix="/auth")
    _maybe_register_blueprint(app, "erp.api", ["bp", "blueprint", "api_bp", "api"], url_prefix="/api")
    _maybe_register_blueprint(app, "erp.views", ["bp", "blueprint", "views_bp", "views"])

    # --- Healthcheck ---
    @app.get("/health")
    def health():
        return jsonify(status="ok")

    # --- Root: send users to an available auth page, otherwise say we're up ---
    @app.route("/", methods=["GET", "HEAD"])
    def _root():
        # Prefer explicit login chooser if present
        for endpoint in ("auth.choose_login", "auth.login", "auth.index"):
            if endpoint in app.view_functions:
                # Avoid redirect loops if someone hits /health with HEAD
                if request.method == "HEAD":
                    return "", 302, {"Location": url_for(endpoint)}
                return redirect(url_for(endpoint))
        # Fallback: plain JSON to confirm app is healthy but no auth blueprint is wired
        return jsonify(
            status="ready",
            note="No auth blueprint endpoint found. Expected one of: auth.choose_login, auth.login, auth.index.",
        )

    # --- Shell context (handy for `flask shell`) ---
    @app.shell_context_processor
    def _shell_ctx():
        return {"db": db}

    return app


# If you ever run `python -m erp.app` locally:
if __name__ == "__main__":
    # NOTE: For local debugging only. In Render, gunicorn runs this via wsgi:app.
    app = create_app()
    # Socket.IO dev server with eventlet
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
