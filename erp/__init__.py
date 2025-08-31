"""Application factory for BERHAN ERP.

This module initialises the core Flask application and wires up common
extensions such as SQLAlchemy for models, Celery for asynchronous tasks and
Flask-Babel for multi-language support.  Blueprints are registered lazily via
``register_blueprints`` to keep the core lightweight.  See
``docs/blueprints.md`` for additional background on the discovery strategy.
"""

from flask import (
    Flask,
    request,
    session,
    Response,
    g,
    render_template,
    current_app,
)
import uuid

from datetime import datetime, UTC
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_socketio import SocketIO, join_room, disconnect
from authlib.integrations.flask_client import OAuth
from typing import Any, Awaitable, cast

try:
    from flask_babel import Babel, get_locale, gettext as _
except Exception:  # pragma: no cover - optional dependency fallback

    class Babel:  # type: ignore[override, no-redef]
        def init_app(self, app, **kwargs):
            return None

    def get_locale() -> str:
        return "en"

    def _(text: str, *args: Any, **kwargs: Any) -> str:
        return text


from celery import Celery, signals
import logging.config
import os
import time
import json
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)
from prometheus_client import multiprocess
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import bleach
from erp.plugins import load_plugins
from .cache import init_cache
from .extensions import db

from config import Config
from db import get_db, redis_client

load_dotenv()


def rate_limit_key():
    user = session.get("user_id")
    token = request.headers.get("Authorization", "")
    return user or token or get_remote_address()


socketio = SocketIO()
oauth = OAuth()
babel = Babel()
celery = Celery(__name__)
limiter = Limiter(key_func=rate_limit_key)
csrf = CSRFProtect()
talisman = Talisman()


@celery.task(name="erp.log_access")
def log_access(
    username: str,
    ip: str,
    device: str,
    timestamp: str,
    correlation_id: str,
) -> None:
    """Persist access log entries asynchronously.

    Failures are logged with the provided ``correlation_id`` instead of
    surfacing to the request cycle.
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            (
                "INSERT INTO access_logs "
                "(username, ip, device, timestamp) "
                "VALUES (%s, %s, %s, %s)"
            ),
            (username, ip, device, timestamp),
        )
        conn.commit()
    except Exception as exc:  # pragma: no cover - best-effort logging
        current_app.logger.warning(
            "failed to record access log",
            extra={"correlation_id": correlation_id, "error": str(exc)},
        )
    finally:
        try:
            cur.close()
            conn.close()
        except Exception as exc:
            current_app.logger.warning("failed to close db connection", exc_info=exc)


@signals.task_failure.connect
def _dead_letter_handler(
    sender: Any | None = None,
    task_id: str | None = None,
    exception: Exception | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    **extra: Any,
) -> None:
    """Push failed Celery tasks to a Redis dead-letter queue."""
    payload = {
        "task": getattr(sender, "name", "") if sender else "",
        "id": task_id,
        "error": str(exception),
        "args": args,
        "kwargs": kwargs,
    }
    redis_client.lpush("dead_letter", json.dumps(payload))


@signals.task_postrun.connect
def _record_queue_depth(*args: Any, **kwargs: Any) -> None:
    """Update queue backlog gauge after each task completes."""
    try:
        import asyncio

        raw = redis_client.llen("celery")
        if isinstance(raw, Awaitable):
            backlog = asyncio.get_event_loop().run_until_complete(raw)
        else:
            backlog = cast(int, raw)
        QUEUE_LAG.labels("celery").set(float(backlog))
    except Exception as exc:
        current_app.logger.warning("queue lag metric update failed", exc_info=exc)


REQUEST_COUNT = Counter(
    "request_count",
    "HTTP Request Count",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram("request_latency_seconds", "Request latency", ["endpoint"])
TOKEN_ERRORS = Counter("token_errors_total", "Invalid or expired token events")
QUEUE_LAG = Gauge("queue_lag", "Celery queue backlog size", ["queue"])
KPI_SALES_MV_AGE = Gauge(
    "kpi_sales_mv_age_seconds",
    "Age of the kpi_sales materialized view in seconds",
)
RATE_LIMIT_REJECTIONS = Counter(
    "rate_limit_rejections_total", "Requests rejected due to rate limiting"
)
GRAPHQL_REJECTS = Counter(
    "graphql_rejects_total",
    "GraphQL queries rejected for depth or complexity limits",
)
AUDIT_CHAIN_BROKEN = Counter(
    "audit_chain_broken_total",
    "Detected breaks in the audit log hash chain",
)
OLAP_EXPORT_SUCCESS = Counter(
    "olap_export_success_total",
    "Number of successful OLAP exports",
)


def create_app():
    # Import inside the factory to avoid circular dependencies during
    # application initialisation where ``app`` imports models which in turn
    # rely on the ``db`` object defined in this module.

    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(Config)
    debug_templates = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.config["TEMPLATES_AUTO_RELOAD"] = debug_templates

    db_url = os.environ.get("DATABASE_URL")
    db_path = os.environ.get("DATABASE_PATH", "erp.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or f"sqlite:///{db_path}"
    # Enable Flask testing mode automatically when running under pytest to
    # simplify conditional logic inside views and avoid noisy side effects.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        app.config["TESTING"] = True

    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {"level": "INFO", "handlers": ["console"]},
        }
    )

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,
    )

    use_fake = os.environ.get("USE_FAKE_REDIS") == "1"
    socketio.init_app(app, message_queue=None if use_fake else app.config["REDIS_URL"])
    oauth.init_app(app)
    db.init_app(app)
    init_cache(app)
    csrf.init_app(app)
    from .app import (
        register_blueprints,
        init_security,
    )  # deferred to avoid circular import

    user_datastore = init_security(app)
    init_celery(app)
    import erp.data_retention  # noqa: F401 - ensure tasks are registered

    storage_uri = "memory://" if use_fake else app.config["REDIS_URL"]
    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    app.config["RATELIMIT_DEFAULT"] = app.config.get(
        "RATE_LIMIT_DEFAULT", "100 per minute"
    )
    limiter.init_app(app)
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"

    def select_locale():
        return (
            session.get("lang")
            or request.accept_languages.best_match(
                app.config["BABEL_SUPPORTED_LOCALES"]
            )
            or app.config["BABEL_DEFAULT_LOCALE"]
        )

    babel.init_app(app, locale_selector=select_locale)
    app.jinja_env.globals["get_locale"] = get_locale
    app.jinja_env.globals.setdefault("_", _)
    if app.config.get("OAUTH_CLIENT_ID"):
        oauth.register(
            "sso",
            client_id=app.config["OAUTH_CLIENT_ID"],
            client_secret=app.config.get("OAUTH_CLIENT_SECRET"),
            access_token_url=app.config.get("OAUTH_TOKEN_URL"),
            authorize_url=app.config.get("OAUTH_AUTH_URL"),
            client_kwargs={"scope": "openid email profile"},
        )

    csp = {
        "default-src": "'self'",
        "script-src": ["'self'"],
        "style-src": ["'self'"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "frame-ancestors": ["'none'"],
    }
    talisman.init_app(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=["script-src"],
        force_https=True,
    )

    @app.before_request
    def _waf():
        if any(v != bleach.clean(v or "", strip=True) for v in request.args.values()):
            return "blocked", 400
        if request.method in {"POST", "PUT", "PATCH"}:
            data = request.get_data(as_text=True, parse_form_data=False)
            if data != bleach.clean(data, strip=True):
                return "blocked", 400

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals["get_locale"] = get_locale

    load_plugins(app)
    register_blueprints(app)
    with app.app_context():
        if app.config.get("TESTING"):
            # Ensure a clean schema for each test run so model changes are
            # reflected and stale tables do not linger between runs.  This
            # avoids issues where previous initialisation scripts created
            # tables missing columns (e.g., ``roles.description``).
            db.drop_all()
            db.create_all()
        for role in ("admin", "pharmacist"):
            if not user_datastore.find_role(role):
                user_datastore.create_role(name=role)
        db.session.commit()

    @socketio.on("connect")
    def _ws_connect(auth):
        token = (auth or {}).get("token")
        org = redis_client.get(f"socket_token:{token}") if token else None
        if not org or int(org) != session.get("org_id"):
            TOKEN_ERRORS.inc()
            disconnect()
            return False
        join_room(f"org_{int(org)}")

    @socketio.on("analytics_ping")
    def _analytics_ping():
        """Emit placeholder analytics to the requester."""
        socketio.emit("analytics_update", {"active_users": 0}, to=request.sid)

    @socketio.on("voice_command")
    def _voice_command(data):
        current_app.logger.info("voice command: %s", data.get("command"))

    @app.context_processor
    def inject_now():
        return {"current_year": datetime.now(UTC).year}

    @app.before_request
    def start_timer():
        g.start_time = time.time()
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        sentry_sdk.set_tag("correlation_id", g.correlation_id)
        # Skip access logs during tests to avoid unintended DB access
        if app.config.get("TESTING"):
            return
        if "logged_in" in session and session["logged_in"]:
            ip = request.remote_addr or ""
            device = request.user_agent.string
            user = (
                session.get("username")
                if session.get("role") != "Client"
                else session.get("tin")
            )
            try:
                log_access.delay(
                    user,
                    ip,
                    device,
                    datetime.now(UTC).isoformat(),
                    g.correlation_id,
                )
            except Exception as exc:  # pragma: no cover - queueing best effort
                current_app.logger.warning(
                    "failed to enqueue access log",
                    extra={"correlation_id": g.correlation_id, "error": str(exc)},
                )

    @app.after_request
    def record_metrics(response):
        endpoint = request.endpoint or "unknown"
        start = getattr(g, "start_time", None)
        if start is not None:
            REQUEST_LATENCY.labels(endpoint).observe(time.time() - start)
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        if response.status_code == 429:
            RATE_LIMIT_REJECTIONS.inc()
        response.headers["X-Correlation-ID"] = g.get("correlation_id", "")
        return response

    @app.route("/metrics")
    def metrics():
        from erp.routes import analytics

        if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
        else:
            registry = REGISTRY

        KPI_SALES_MV_AGE.set(analytics.kpi_staleness_seconds())
        try:
            QUEUE_LAG.labels("celery").set(redis_client.llen("celery"))
        except Exception as exc:
            current_app.logger.warning("queue lag metric update failed", exc_info=exc)
        return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

    @app.errorhandler(401)
    def _401(error):
        return (
            render_template(
                "errors/401.html",
                code=401,
                message=getattr(error, "description", None),
            ),
            401,
        )

    @app.errorhandler(403)
    def _403(error):
        return (
            render_template(
                "errors/403.html",
                code=403,
                message=getattr(error, "description", None),
            ),
            403,
        )

    @app.errorhandler(404)
    def _404(error):
        return (
            render_template(
                "errors/404.html",
                code=404,
                message=getattr(error, "description", None),
            ),
            404,
        )

    @app.errorhandler(500)
    def _500(error):
        current_app.logger.exception("Unhandled exception", exc_info=error)
        return (
            render_template(
                "errors/500.html",
                code=500,
                message=getattr(error, "description", None),
            ),
            500,
        )

    return app


def init_celery(app):
    """Configure Celery to run tasks within app context."""
    celery.conf.broker_url = app.config.get("CELERY_BROKER_URL")
    celery.conf.result_backend = app.config.get("CELERY_RESULT_BACKEND")

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
