from flask import Flask, request, session, Response, g, render_template
import uuid
import importlib
import pkgutil

from datetime import datetime, UTC
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_socketio import SocketIO, join_room, disconnect
from authlib.integrations.flask_client import OAuth
from flask_babel import Babel, _, get_locale
import logging.config
import os
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from erp.plugins import load_plugins

from config import Config
from db import get_db, redis_client

load_dotenv()

def rate_limit_key():
    user = session.get('user_id')
    token = request.headers.get('Authorization', '')
    return user or token or get_remote_address()

socketio = SocketIO()
oauth = OAuth()
babel = Babel()
limiter = None

REQUEST_COUNT = Counter('request_count', 'HTTP Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['endpoint'])
TOKEN_ERRORS = Counter('token_errors_total', 'Invalid or expired token events')
QUEUE_LAG = Gauge('queue_lag', 'Celery queue backlog size', ['queue'])


def _ensure_base_tables() -> None:
    """Create minimal tables required for test isolation.

    The repository relies on migrations for full schema management, but the
    test suite uses a lightweight SQLite database. To keep tests hermetic and
    enforce row-level security expectations, we create the ``inventory_items``
    table on startup if it is missing. This covers both SQLite and PostgreSQL
    backends without requiring a running migration step."""

    conn = get_db()
    cur = conn.cursor()
    try:
        if getattr(conn, "_dialect", None) and conn._dialect.name == "sqlite":
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL
                )
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id SERIAL PRIMARY KEY,
                    org_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL
                )
                """
            )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config.from_object(Config)
    # Enable Flask testing mode automatically when running under pytest to
    # simplify conditional logic inside views and avoid noisy side effects.
    if os.environ.get('PYTEST_CURRENT_TEST'):
        app.config['TESTING'] = True

    logging.config.dictConfig({
        'version': 1,
        'formatters': {'default': {'format': '%(asctime)s %(levelname)s %(name)s %(message)s'}},
        'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'default'}},
        'root': {'level': 'INFO', 'handlers': ['console']},
    })

    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'), integrations=[FlaskIntegration()], traces_sample_rate=1.0)

    use_fake = os.environ.get('USE_FAKE_REDIS') == '1'
    socketio.init_app(app, message_queue=None if use_fake else app.config['REDIS_URL'])
    oauth.init_app(app)
    global limiter
    storage_uri = 'memory://' if use_fake else app.config['REDIS_URL']
    limiter = Limiter(
        key_func=rate_limit_key,
        storage_uri=storage_uri,
        default_limits=[app.config.get('RATE_LIMIT_DEFAULT', '100 per minute')],
    )
    limiter.init_app(app)
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    def select_locale():
        return (
            session.get('lang')
            or request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])
            or app.config['BABEL_DEFAULT_LOCALE']
        )

    babel.init_app(app, locale_selector=select_locale)
    app.jinja_env.globals['get_locale'] = get_locale
    if app.config.get('OAUTH_CLIENT_ID'):
        oauth.register(
            'sso',
            client_id=app.config['OAUTH_CLIENT_ID'],
            client_secret=app.config.get('OAUTH_CLIENT_SECRET'),
        
            access_token_url=app.config.get('OAUTH_TOKEN_URL'),
            authorize_url=app.config.get('OAUTH_AUTH_URL'),
            client_kwargs={'scope': 'openid email profile'},
        )

    Talisman(app, content_security_policy=None, force_https=True)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals['get_locale'] = get_locale

    load_plugins(app)
    register_blueprints(app)
    _ensure_base_tables()

    @socketio.on('connect')
    def _ws_connect(auth):
        token = (auth or {}).get('token')
        org = redis_client.get(f"socket_token:{token}") if token else None
        if not org or int(org) != session.get('org_id'):
            TOKEN_ERRORS.inc()
            disconnect()
            return False
        join_room(f"org_{int(org)}")

    

    @app.context_processor
    def inject_now():
        return {'current_year': datetime.now(UTC).year}

    @app.before_request
    def start_timer():
        g.start_time = time.time()
        g.correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        sentry_sdk.set_tag('correlation_id', g.correlation_id)
        # Skip access log writes during tests to avoid unintended database access
        if app.config.get('TESTING'):
            return
        if 'logged_in' in session and session['logged_in']:
            ip = request.remote_addr
            device = request.user_agent.string
            conn = get_db()
            cur = conn.cursor()
            user = session.get('username') if session.get('role') != 'Client' else session.get('tin')
            try:
                cur.execute(
                    'INSERT INTO access_logs (username, ip, device, timestamp) VALUES (%s, %s, %s, %s)',
                    (user, ip, device, datetime.now())
                )
                conn.commit()
            except Exception:
                conn.rollback()
            finally:
                cur.close()
                conn.close()

    @app.after_request
    def record_metrics(response):
        endpoint = request.endpoint or 'unknown'
        REQUEST_LATENCY.labels(endpoint).observe(time.time() - g.start_time)
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        response.headers['X-Correlation-ID'] = g.get('correlation_id', '')
        return response

    @app.route('/metrics')
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.errorhandler(401)
    def _401(error):
        return render_template('errors/401.html', code=401, message=getattr(error, 'description', None)), 401

    @app.errorhandler(403)
    def _403(error):
        return render_template('errors/403.html', code=403, message=getattr(error, 'description', None)), 403

    @app.errorhandler(404)
    def _404(error):
        return render_template('errors/404.html', code=404, message=getattr(error, 'description', None)), 404

    @app.errorhandler(500)
    def _500(error):
        return render_template('errors/500.html', code=500, message=getattr(error, 'description', None)), 500

    return app


def register_blueprints(app):
    """Auto-discover and register blueprints exposed as `bp`."""

    def _scan(package: str):
        try:
            pkg = importlib.import_module(package)
        except ModuleNotFoundError:
            return
        for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + '.'):
            if ispkg:
                _scan(modname)
            else:
                try:
                    mod = importlib.import_module(modname)
                    bp = getattr(mod, 'bp', None)
                    if bp is not None:
                        app.register_blueprint(bp)
                except Exception:
                    continue

    _scan('erp.routes')
    _scan('plugins')


