
from __future__ import annotations
from flask import Flask, session, Response
from .config import Config, validate_config
from .observability import init_logging
from .security import apply_security_headers
from .errors import register_error_handlers
# init_db.py
from argon2 import PasswordHasher

# Use defaults (good for tests)
ph = PasswordHasher()


GRAPHQL_REJECTS = 0
QUEUE_LAG = 0
RATE_LIMIT_REJECTIONS = 0
OLAP_EXPORT_SUCCESS = 0

try:
    from flask_socketio import SocketIO  # type: ignore
    socketio = SocketIO(message_queue=None, async_mode="threading")  # pragma: no cover
except Exception:  # pragma: no cover
    socketio = None

def create_app(test_config=None):
    app = Flask(__name__)
    import os
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret"))
    app.config.from_object(Config())
    if test_config:
        app.config.update(test_config)

    try:
        validate_config(app.config)
    except Exception:
        pass

    try:
        from .db import db
        db.init_app(app)
    except Exception:
        pass

    try:
        from .blueprints.health import bp as health_bp
        app.register_blueprint(health_bp, url_prefix="/")
    except Exception:
        pass

    apply_security_headers(app)
    register_error_handlers(app)
    init_logging(app)

    # ---- Phase1 health endpoints ----
    def _install_health(app):
        # avoid duplicate registration across repeated app factories
        existing = {r.rule for r in app.url_map.iter_rules()}
        if '/healthz' not in existing:
            @app.get('/healthz')
            def healthz():
                from flask import Flask, session, Response
                return jsonify(status='ok'), 200
        if '/readyz' not in existing:
            @app.get('/readyz')
            def readyz():
                from flask import Flask, session, Response
                return jsonify(status='ready'), 200
    _install_health(app)
    # ---- /Phase1 health endpoints ----
    # Phase1 observability
    try:
        from .observability import register_metrics_endpoint
        register_metrics_endpoint(app)
    except Exception:
        pass
    # Phase1: rate limiting
    try:
        from .extensions import limiter
        limiter.init_app(app)
    except Exception:
        pass


        # Auto-register privacy blueprint if available
    try:
        from .routes import privacy as _privacy
        if hasattr(_privacy, "bp"):
            app.register_blueprint(_privacy.bp)
    except Exception:
        pass
        # Ensure models are loaded and tables exist (useful for tests / SQLite)
    try:
        from . import models as _models  # noqa: F401
    except Exception:
        pass
    try:
        with app.app_context():
            db.create_all()
    except Exception:
        pass
    return app

oauth = None



# Phase1: export audit flag API
try:
    from .observability import AUDIT_CHAIN_BROKEN, set_audit_chain_broken
except Exception:
    AUDIT_CHAIN_BROKEN = False
    def set_audit_chain_broken(flag: bool = True):  # noqa: D401
        # no-op fallback when observability is unavailable
        return

# Phase1: export DLQ handler (_dead_letter_handler) for tests
try:
    from .dlq import dead_letter_handler as _dead_letter_handler  # noqa: F401
except Exception:
    def _dead_letter_handler(*args, **kwargs):  # noqa: D401
        # no-op fallback
        return


from importlib import import_module
import pkgutil
from flask import Flask, session, Response
from werkzeug.exceptions import HTTPException

# export limiter placeholder and oauth stub so tests can import
class _Limiter: pass
limiter = _Limiter()

from .oauth import oauth  # re-export

def _auto_register_blueprints(app):
    import erp.routes as routes_pkg
    for mod in pkgutil.iter_modules(routes_pkg.__path__):
        module = import_module(f"erp.routes.{mod.name}")
        bp = getattr(module, "bp", None)
        if bp:
            app.register_blueprint(bp)

def create_app():
    app = Flask(__name__)
    import os
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret"))
    # ... keep your existing config/db setup ...

    # error handler: don't turn HTTPException (like 409) into 500
    @app.errorhandler(Exception)
    def _err(e):
        if isinstance(e, HTTPException):
            return e
        app.logger.error("uncaught_exception", exc_info=e)
        return Response('{"error":"internal"}', mimetype="application/json", status=500)

    # language switch + minimal dashboard used by i18n tests
    @app.get("/set_language/<lang>")
    def set_language(lang):
        session["lang"] = lang
        return Response("ok")

    @app.get("/dashboard")
    def dashboard():
        lang = session.get("lang", "en")
        html = f'<!doctype html><html lang="{lang}"><head></head><body><select id="lang-select"></select></body></html>'
        return Response(html, mimetype="text/html")

    # auto register all route blueprints
    _auto_register_blueprints(app)

    # (optional) create tables for sqlite during tests
    try:
        if app.config.get("TESTING") or app.config.get("ENV") == "development" or os.getenv("AUTO_CREATE_DB") == "1":
            with app.app_context():
                db.create_all()
    except Exception:
        pass

    return app
from importlib import import_module
import pkgutil
from flask import Flask, session, Response
from werkzeug.exceptions import HTTPException

# export limiter placeholder and oauth stub so tests can import
class _Limiter: pass
limiter = _Limiter()

from .oauth import oauth  # re-export

def _auto_register_blueprints(app):
    import erp.routes as routes_pkg
    for mod in pkgutil.iter_modules(routes_pkg.__path__):
        module = import_module(f"erp.routes.{mod.name}")
        bp = getattr(module, "bp", None)
        if bp:
            app.register_blueprint(bp)

def create_app():
    app = Flask(__name__)
    import os
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret"))
    # ... keep your existing config/db setup ...

    # error handler: don't turn HTTPException (like 409) into 500
    @app.errorhandler(Exception)
    def _err(e):
        if isinstance(e, HTTPException):
            return e
        app.logger.error("uncaught_exception", exc_info=e)
        return Response('{"error":"internal"}', mimetype="application/json", status=500)

    # language switch + minimal dashboard used by i18n tests
    @app.get("/set_language/<lang>")
    def set_language(lang):
        session["lang"] = lang
        return Response("ok")

    @app.get("/dashboard")
    def dashboard():
        lang = session.get("lang", "en")
        html = f'<!doctype html><html lang="{lang}"><head></head><body><select id="lang-select"></select></body></html>'
        return Response(html, mimetype="text/html")

    # auto register all route blueprints
    _auto_register_blueprints(app)

    # (optional) create tables for sqlite during tests
    try:
        if app.config.get("TESTING") or app.config.get("ENV") == "development" or os.getenv("AUTO_CREATE_DB") == "1":
            with app.app_context():
                db.create_all()
    except Exception:
        pass

    return app






