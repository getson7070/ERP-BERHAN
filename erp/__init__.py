from flask import Flask, request, session
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
from flask_talisman import Talisman

from config import Config
from db import get_db

load_dotenv()


def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)

    Talisman(app, content_security_policy=None, force_https=True)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat(" "))

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
    def log_access():
        if 'logged_in' in session and session['logged_in']:
            ip = request.remote_addr
            device = request.user_agent.string
            conn = get_db()
            user = session.get('username') if session.get('role') != 'Client' else session.get('tin')
            conn.execute(
                'INSERT INTO access_logs (user, ip, device, timestamp) VALUES (?, ?, ?, ?)',
                (user, ip, device, datetime.now())
            )
            conn.commit()
            conn.close()

    return app
