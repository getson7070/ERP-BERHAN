from flask import Blueprint, render_template, redirect, url_for, session
from celery import Celery
from celery.schedules import crontab
from datetime import datetime

from db import get_db
from erp.utils import login_required, roles_required
from erp import socketio
from flask_socketio import emit

bp = Blueprint('analytics', __name__)

celery = Celery(__name__)


def fetch_kpis():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM orders WHERE status = ?', ('pending',))
    pending_orders = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM maintenance WHERE status = ?', ('pending',))
    pending_maintenance = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tenders WHERE status = 'expired'")
    expired_tenders = cur.fetchone()[0]
    cur.execute(
        "SELECT COALESCE(SUM(total_sales),0) FROM kpi_sales WHERE month = DATE_TRUNC('month', CURRENT_DATE)"
    )
    monthly_sales = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {
        'pending_orders': pending_orders,
        'pending_maintenance': pending_maintenance,
        'expired_tenders': expired_tenders,
        'monthly_sales': float(monthly_sales or 0),
    }

@bp.record_once
def init_celery(state):
    app = state.app
    celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    celery.conf.beat_schedule = {
        'generate-daily-report': {
            'task': 'analytics.generate_report',
            'schedule': crontab(hour=0, minute=0),
        },
        'expire-due-tenders': {
            'task': 'analytics.expire_tenders',
            'schedule': crontab(hour=1, minute=0),
        },
        'refresh-kpi-sales': {
            'task': 'analytics.refresh_kpis',
            'schedule': crontab(minute='*/30'),
        },
    }


@bp.route('/analytics/dashboard')
@login_required
@roles_required('Management')
def dashboard():
    kpis = fetch_kpis()
    role = session.get('role')
    permissions = session.get('permissions', [])
    return render_template(
        'analytics/dashboard.html',
        role=role,
        permissions=permissions,
        pending_orders=kpis['pending_orders'],
        pending_maintenance=kpis['pending_maintenance'],
        expired_tenders=kpis['expired_tenders'],
        monthly_sales=kpis['monthly_sales'],
    )


@socketio.on('connect')
def push_kpis():
    emit('kpi_update', fetch_kpis())


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


@celery.task
def expire_tenders():
    conn = get_db()
    conn.execute(
        "UPDATE tenders SET status = 'expired' WHERE due_date < DATE('now') AND status IS NULL"
    )
    conn.commit()
    conn.close()


@celery.task
def refresh_kpis():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_sales')
    conn.commit()
    cur.close()
    conn.close()
    socketio.emit('kpi_update', fetch_kpis())
