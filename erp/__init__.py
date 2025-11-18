"""ERP package root.

This package bundles the various modules of the ERP‑BERHAN system, including
finance, CRM, sales, user management and core data models.  The modules are
organised into subpackages with clearly defined responsibilities.  See the
documentation for details on each module’s functionality.
"""

from flask import Flask, jsonify
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

from db import redis_client  # type: ignore

from .db import db as db
from .dlq import _dead_letter_handler
from .extensions import cache, init_extensions, limiter, login_manager, mail
from .metrics import (
    AUDIT_CHAIN_BROKEN,
    DLQ_MESSAGES,
    GRAPHQL_REJECTS,
    QUEUE_LAG,
    RATE_LIMIT_REJECTIONS,
)
from .socket import socketio
from .security import apply_security

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _load_config(app: Flask) -> None:
    """Populate ``app.config`` from the canonical Config object or env vars."""

    try:
        from erp.config import Config as ERPConfig  # type: ignore
    except ImportError:  # pragma: no cover - optional module in deployments
        ERPConfig = None  # type: ignore

    if ERPConfig is not None:
        diff --git a/erp/__init__.py b/erp/__init__.py
index e74c53ce1d00d9e97bdb547056a5246c25da3a0f..1a3530e2fff51a0fbf4ca4f4c96de9eb22e6d393 100644
--- a/erp/__init__.py
+++ b/erp/__init__.py
@@ -44,79 +44,97 @@ def _load_config(app: Flask) -> None:
         app.config.from_object(ERPConfig)
         return
 
     try:
         from config import Config as InstanceConfig  # type: ignore
     except ImportError:  # pragma: no cover - fallback only hit in minimal envs
         InstanceConfig = None  # type: ignore
 
     if InstanceConfig is not None:
         app.config.from_object(InstanceConfig)
         return
 
     # Fallback configuration mirrors the documented deployment defaults.
     database_url = os.environ.get("DATABASE_URL")
     if not database_url:
         database_path = os.environ.get("DATABASE_PATH")
         if database_path:
             database_url = f"sqlite:///{database_path}"
         else:
             database_url = "sqlite:///local.db"
 
     app.config.update(
         SECRET_KEY=os.environ.get("SECRET_KEY", "change-me"),
         SQLALCHEMY_DATABASE_URI=database_url,
         SQLALCHEMY_TRACK_MODIFICATIONS=False,
+        # Sensible defaults to avoid dev-time warnings while still keeping
+        # security-focused settings (short-lived, in-memory cache by default).
+        CACHE_TYPE=os.environ.get("CACHE_TYPE", "SimpleCache"),
+        CACHE_DEFAULT_TIMEOUT=int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300)),
         SESSION_COOKIE_SECURE=True,
         SESSION_COOKIE_HTTPONLY=True,
         SESSION_COOKIE_SAMESITE="Lax",
         REMEMBER_COOKIE_SECURE=True,
         REMEMBER_COOKIE_HTTPONLY=True,
         WTF_CSRF_TIME_LIMIT=None,
     )
 
 
 # ---------------------------------------------------------------------------
 # Blueprint discovery
 # ---------------------------------------------------------------------------
 
 _MANIFEST = Path(__file__).resolve().parent.parent / "blueprints_dedup_manifest.txt"
 _DEFAULT_BLUEPRINT_MODULES = [
     "erp.main",
     "erp.web",
     "erp.views_ui",
     "erp.routes.main",
     "erp.routes.dashboard_customize",
     "erp.routes.analytics",
+    "erp.routes.auth",
+    "erp.routes.approvals",
+    "erp.routes.maintenance",
+    "erp.routes.orders",
+    "erp.sales.routes",
+    "erp.marketing.routes",
+    "erp.routes.inventory",
+    "erp.routes.finance",
+    "erp.routes.hr",
+    "erp.routes.crm",
+    "erp.supplychain.routes",
+    "erp.routes.report_builder",
     "erp.blueprints.inventory",
 ]
 
 _EXCLUDED_BLUEPRINT_MODULES = {
     "erp.health_checks",
     "erp.blueprints.health_compat",
     "erp.ops.health",
     "erp.ops.status",
+    "erp.finance.banking",  # legacy banking blueprint defining duplicate models
+    "erp.crm.routes",  # legacy CRM blueprint colliding with the upgraded module
 }
 
 
 def _iter_blueprint_modules() -> Iterable[str]:
     """Yield dotted module paths that are expected to expose a Blueprint."""
 
     seen: set[str] = set()
 
     if _MANIFEST.exists():
         for line in _MANIFEST.read_text(encoding="utf-8").splitlines():
             line = line.strip()
             if not line or line.startswith("#") or ":" not in line:
                 continue
             if line.startswith("CHOSEN") or line.startswith("SKIPPED"):
                 continue
             if line.startswith("- "):
                 try:
                     _, remainder = line.split(":", 1)
                 except ValueError:
                     continue
                 module = remainder.strip().split()[0]
                 if "." in module:
                     module = module.rsplit(".", 1)[0]
                 if module and module not in seen:
                     seen.add(module)
@@ -217,50 +235,73 @@ def register_blueprints(app: Flask) -> None:
 
 def _register_core_routes(app: Flask) -> None:
     routes = {rule.rule for rule in app.url_map.iter_rules()}
 
     if "/healthz" not in routes:
 
         @app.get("/healthz")
         def healthz():
             return jsonify(status="ok"), 200
 
 
 def create_app(config_object: str | None = None) -> Flask:
     """Application factory used by Flask, Celery, and CLI tooling."""
 
     app = Flask(__name__, instance_relative_config=False)
     app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
 
     if config_object:
         app.config.from_object(config_object)
     else:
         _load_config(app)
 
     init_extensions(app)
     apply_security(app)
     register_blueprints(app)
+    # Guarantee marketing endpoints are present even when manifest skips them
+    try:  # pragma: no cover - defensive registration
+        from erp.marketing import routes as marketing_routes
+        from erp.marketing.routes import bp as marketing_bp
+
+        if "marketing" not in app.blueprints:
+            app.register_blueprint(marketing_bp)
+        if "marketing.visits" not in app.view_functions:
+            app.add_url_rule(
+                "/marketing/visits",
+                endpoint="marketing.visits",
+                view_func=marketing_routes.visits,
+                methods=["GET", "POST"],
+            )
+        if "marketing.events" not in app.view_functions:
+            app.add_url_rule(
+                "/marketing/events",
+                endpoint="marketing.events",
+                view_func=marketing_routes.events,
+                methods=["GET", "POST"],
+            )
+    except Exception as exc:
+        LOGGER.warning("Marketing blueprint registration failed: %s", exc)
     _register_core_routes(app)
 
     # Ensure models are imported for Alembic autogenerate & shell usage.
     try:  # pragma: no cover - imports for side effects only
         importlib.import_module("erp.models")
     except Exception as exc:
         LOGGER.debug("Model import failed during boot: %s", exc)
 
     return app
 
 
 __all__ = [
     "create_app",
     "register_blueprints",
     "db",
     "cache",
     "mail",
     "limiter",
     "login_manager",
     "redis_client",
     "socketio",
     "QUEUE_LAG",
     "RATE_LIMIT_REJECTIONS",
     "GRAPHQL_REJECTS",
     "AUDIT_CHAIN_BROKEN",
    "DLQ_MESSAGES",
    "_dead_letter_handler",
]
__all__ = []  # exported names are defined in subpackages
