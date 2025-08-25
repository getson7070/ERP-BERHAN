from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
import os
from celery import Celery
from celery.schedules import crontab
from datetime import datetime
from db import get_db

analytics_bp = Blueprint('analytics', __name__)

celery = Celery(
    __name__,
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('choose_login'))
        return f(*args, **kwargs)
    return wrap

@analytics_bp.record_once
def init_celery(state):
    app = state.app
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    celery.conf.beat_schedule = {
        'generate-daily-report': {
            'task': 'blueprints.analytics.generate_report',
            'schedule': crontab(hour=0, minute=0),
        }
    }

@analytics_bp.route('/analytics/dashboard')
@login_required
def dashboard():
    conn = get_db()
    pending_orders = conn.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"').fetchone()[0]
    pending_maintenance = conn.execute('SELECT COUNT(*) FROM maintenance WHERE status = "pending"').fetchone()[0]
    conn.close()
    role = session.get('role')
    permissions = session.get('permissions', [])
    return render_template(
        'analytics/dashboard.html',
        role=role,
        permissions=permissions,
        pending_orders=pending_orders,
        pending_maintenance=pending_maintenance,
    )

@celery.task
def generate_report():
    conn = get_db()
    cur = conn.cursor()
    orders = cur.execute('SELECT status, COUNT(*) FROM orders GROUP BY status').fetchall()
    maintenance = cur.execute('SELECT status, COUNT(*) FROM maintenance GROUP BY status').fetchall()
    filename = f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, 'w') as f:
        f.write('Orders\n')
        for status, count in orders:
            f.write(f"{status},{count}\n")
        f.write('Maintenance\n')
        for status, count in maintenance:
            f.write(f"{status},{count}\n")
    conn.close()
    return filename
