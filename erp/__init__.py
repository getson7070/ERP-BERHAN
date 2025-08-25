from flask import Flask, request, session, Response, g
from datetime import datetime
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_socketio import SocketIO
from authlib.integrations.flask_client import OAuth
from flask_babel import Babel, _, get_locale
import logging.config
import os
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config import Config
from db import get_db

load_dotenv()

socketio = SocketIO()
oauth = OAuth()
babel = Babel()

REQUEST_COUNT = Counter('request_count', 'HTTP Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['endpoint'])


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='../templates')
    app.config.from_object(Config)

    logging.config.dictConfig({
        'version': 1,
        'formatters': {'default': {'format': '%(asctime)s %(levelname)s %(name)s %(message)s'}},
        'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'default'}},
        'root': {'level': 'INFO', 'handlers': ['console']},
    })

    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'), integrations=[FlaskIntegration()], traces_sample_rate=1.0)

    socketio.init_app(app, message_queue=app.config['REDIS_URL'])
    oauth.init_app(app)
    babel.init_app(app, locale_selector=lambda: session.get('lang') or request.accept_languages.best_match(app.config['LANGUAGES']))
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


    from .routes import auth, orders, tenders, main, analytics
    app.register_blueprint(auth.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(tenders.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(main.bp)

    @app.context_processor
    def inject_now():
        return {'current_year': datetime.utcnow().year}

    @app.before_request
    def start_timer():
        g.start_time = time.time()
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
        return response

    @app.route('/metrics')
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    return app
