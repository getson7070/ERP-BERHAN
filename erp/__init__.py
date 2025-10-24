from __future__ import annotations
import importlib, pkgutil, os
from typing import Any
from flask import Flask, Response

from .extensions import csrf, limiter, login_manager, db

def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def _h(resp: Response) -> Response:
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        # Minimal CSP safe default; relax per-page when needed
        resp.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'")
        return resp

def _autodiscover_and_register_blueprints(app: Flask) -> None:
    # Import any module in erp.routes that exposes a Flask Blueprint named `bp`
    try:
        import erp.routes as routes_pkg  # type: ignore
        for m in [m.name for m in pkgutil.iter_modules(routes_pkg.__path__)]:
            try:
                mod = importlib.import_module(f"erp.routes.{m}")
                bp = getattr(mod, "bp", None)
                if bp is not None:
                    app.register_blueprint(bp)
            except Exception:
                # Keep resilient: a faulty optional module shouldn't break app startup
                continue
    except Exception:
        pass

def create_app(config: dict | None = None) -> Flask:
    app = Flask("erp")
    # Config defaults; allow env/instance override
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret"))
    app.config.setdefault("JSONIFY_PRETTYPRINT_REGULAR", False)

    # Late bind extensions
    csrf.init_app(app)
    limiter.init_app(app)
    try:
        login_manager.init_app(app)  # type: ignore[attr-defined]
    except Exception:
        pass

    # Register blueprints
    _autodiscover_and_register_blueprints(app)

    # Security headers
    _register_security_headers(app)

    # Fallback healthz if route package missing
    @app.get("/healthz")
    def _healthz():
        return {"ok": True}

    return app
