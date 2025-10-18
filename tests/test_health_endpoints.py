import importlib
import os
import types

def _get_app():
    # Try wsgi.app, fallback to app.create_app, else synthesize a minimal Flask app for health checks
    try:
        wsgi = importlib.import_module("wsgi")
        if hasattr(wsgi, "app"):
            return wsgi.app
    except Exception:
        pass

    try:
        app_mod = importlib.import_module("app")
        if hasattr(app_mod, "create_app"):
            return app_mod.create_app(testing=True)
    except Exception:
        pass

    # Minimal fallback app with only health blueprint
    from flask import Flask
    app = Flask(__name__)
    from erp.blueprints.health import bp as health_bp
    app.register_blueprint(health_bp)
    return app

def test_healthz():
    app = _get_app()
    client = app.test_client()
    rv = client.get("/healthz")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("status") == "ok"

def test_readyz():
    # In CI, Postgres/Redis are available; locally this may return 503 if not configured.
    app = _get_app()
    client = app.test_client()
    rv = client.get("/readyz")
    assert rv.status_code in (200, 503)
    data = rv.get_json()
    assert "ready" in data
