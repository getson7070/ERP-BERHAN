"""Application factory for BERHAN ERP.

This module initialises the core Flask application and wires up common
extensions such as SQLAlchemy for models, Celery for asynchronous tasks and
Flask-Babel for multi-language support.  Blueprints are registered lazily via
``register_blueprints`` to keep the core lightweight.  See
``docs/blueprints.md`` for additional background on the discovery strategy.
"""

import os
import uuid
from datetime import UTC, datetime
from typing import Any, Awaitable, cast
from urllib.parse import parse_qsl

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, Response, current_app, g, render_template, request, session
from flask_compress import Compress
from flask_socketio import SocketIO, disconnect, join_room
from flask_talisman import Talisman

try:
    from flask_babel import Babel, get_locale
    from flask_babel import gettext as _
except Exception:  # pragma: no cover - optional dependency fallback

    class Babel:  # type: ignore[override, no-redef]
        def init_app(self, app, **kwargs):
            return None

    def get_locale() -> str:
        return "en"

    def _(text: str, *args: Any, **kwargs: Any) -> str:
        return text


import json
import logging
import logging.config
import time

import bleach  # type: ignore[import-untyped]
import sentry_sdk
from celery import Celery, signals
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    generate_latest,
    multiprocess,
)
from sentry_sdk.integrations.flask import FlaskIntegration
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

from config import Config
from db import get_db, redis_client
from erp.plugins import load_plugins

from .cache import init_cache
from .extensions import db
from .observability import (
    APDEX_FRUSTRATED,
    APDEX_SATISFIED,
    APDEX_SCORE,
    APDEX_THRESHOLD,
    APDEX_TOLERATING,
)
from .observability import AUDIT_CHAIN_BROKEN as AUDIT_CHAIN_BROKEN
from .observability import GRAPHQL_REJECTS as GRAPHQL_REJECTS
from .observability import KPI_SALES_MV_AGE
from .observability import OLAP_EXPORT_SUCCESS as OLAP_EXPORT_SUCCESS
from .observability import (
    QUEUE_LAG,
    RATE_LIMIT_REJECTIONS,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    TOKEN_ERRORS,
    configure_opentelemetry,
)

load_dotenv()


def rate_limit_key():
    user = session.get("user_id")
    token = request.headers.get("Authorization", "")
    return user or token or get_remote_address()


class RequestIdFilter(logging.Filter):
    """Attach the current request correlation ID to log records."""

    def filter(
        self, record: logging.LogRecord
    ) -> bool:  # pragma: no cover - simple filter
        setattr(record, "request_id", getattr(g, "correlation_id", None))
        return True


class JsonFormatter(logging.Formatter):
    """Render logs as structured JSON with optional request identifiers."""

    def format(
        self, record: logging.LogRecord
    ) -> str:  # pragma: no cover - simple formatter
        log = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        req_id = getattr(record, "request_id", None)
        if req_id:
            log["request_id"] = req_id
        trace_id = getattr(record, "otelTraceID", None)
        if trace_id:
            log["trace_id"] = trace_id
        span_id = getattr(record, "otelSpanID", None)
        if span_id:
            log["span_id"] = span_id
        return json.dumps(log)


socketio = SocketIO()
oauth = OAuth()
babel = Babel()
celery = Celery(__name__)
limiter = Limiter(key_func=rate_limit_key)
csrf = CSRFProtect()
talisman = Talisman()
compress = Compress()


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


def create_app():
    # Import inside the factory to avoid circular dependencies during
    # application initialisation where ``app`` imports models which in turn
    # rely on the ``db`` object defined in this module.

    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(Config)
    debug_templates = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.config["TEMPLATES_AUTO_RELOAD"] = debug_templates
    app.config["APDEX_LATENCY_THRESHOLD"] = APDEX_THRESHOLD

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
            "filters": {"request_id": {"()": RequestIdFilter}},
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["request_id"],
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
    if os.getenv("ENV") == "production":
        if use_fake:
            raise RuntimeError("USE_FAKE_REDIS must be disabled in production")
        if not os.environ.get("REDIS_URL"):
            raise RuntimeError("REDIS_URL is required in production")
    socketio.init_app(app, message_queue=None if use_fake else app.config["REDIS_URL"])
    oauth.init_app(app)
    db.init_app(app)
    init_cache(app)
    configure_opentelemetry(app, db)
    compress.init_app(app)
    csrf.init_app(app)
    from .app import (  # deferred to avoid circular import
        init_security,
        register_blueprints,
    )

    user_datastore = init_security(app)
    init_celery(app)
    import erp.data_retention  # noqa: F401 - ensure tasks are registered

    storage_uri = "memory://" if use_fake else app.config["REDIS_URL"]
    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    app.config["RATELIMIT_DEFAULT"] = app.config.get(
        "RATE_LIMIT_DEFAULT", "100 per minute"
    )
    limiter.init_app(app)
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(
        app.root_path, "..", "translations"
    )

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
        # Workbox modules are fetched from Google's CDN, so it must be
        # explicitly whitelisted in the policy.
        "script-src": ["'self'", "https://storage.googleapis.com"],
        "style-src": ["'self'"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'", "https://storage.googleapis.com"],
        "frame-ancestors": ["'none'"],
    }
    talisman.init_app(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=["script-src"],
        force_https=True,
        strict_transport_security_preload=True,
        referrer_policy="no-referrer",
        permissions_policy={
            "geolocation": "()",
            "microphone": "()",
            "camera": "()",
        },
    )

    @app.after_request
    def add_cache_headers(response: Response) -> Response:
        if request.endpoint == "static":
            response.headers.setdefault(
                "Cache-Control", "public, max-age=31536000, immutable"
            )
        return response

    @app.after_request
    def _set_coop_coep(response: Response) -> Response:
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        return response

    @app.before_request
    def _waf():
        if any(v != bleach.clean(v or "", strip=True) for v in request.args.values()):
            return "blocked", 400
        if request.method in {"POST", "PUT", "PATCH"} and request.mimetype in {
            "application/json",
            "text/plain",
            "application/x-www-form-urlencoded",
        }:
            data = request.get_data(as_text=True, parse_form_data=False)
            if request.mimetype == "application/x-www-form-urlencoded":
                for _, value in parse_qsl(data, keep_blank_values=True):
                    if value != bleach.clean(value or "", strip=True):
                        return "blocked", 400
            elif data != bleach.clean(data, strip=True):
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
        inspector = inspect(db.engine)
        if inspector.has_table("roles"):
            try:
                for role in ("Admin", "Manager", "Staff", "Auditor"):
                    if not user_datastore.find_role(role):
                        user_datastore.create_role(name=role)
                db.session.commit()
            except (ProgrammingError, OperationalError):
                db.session.rollback()

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
            duration = time.time() - start
            REQUEST_LATENCY.labels(endpoint).observe(duration)
            if duration <= APDEX_THRESHOLD / 2:
                APDEX_SATISFIED.inc()
            elif duration <= APDEX_THRESHOLD:
                APDEX_TOLERATING.inc()
            else:
                APDEX_FRUSTRATED.inc()
            total = (
                APDEX_SATISFIED._value.get()
                + APDEX_TOLERATING._value.get()
                + APDEX_FRUSTRATED._value.get()
            )
            if total:
                score = (
                    APDEX_SATISFIED._value.get() + 0.5 * APDEX_TOLERATING._value.get()
                ) / total
                APDEX_SCORE.set(score)
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        if response.status_code == 429:
            RATE_LIMIT_REJECTIONS.inc()
        response.headers["X-Correlation-ID"] = g.get("correlation_id", "")
        return response

    @app.route("/metrics")
    def metrics():
        token = os.environ.get("METRICS_AUTH_TOKEN")
        auth_header = request.headers.get("Authorization", "")
        if token and auth_header != f"Bearer {token}":
            return Response(status=401)

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
