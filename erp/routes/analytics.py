from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from celery import Celery
from celery.schedules import crontab
from datetime import datetime
from sqlalchemy import text

from db import get_db
from erp.utils import login_required, roles_required
from erp.audit import log_audit
from erp import socketio
from flask_socketio import emit

bp = Blueprint('analytics', __name__)

celery = Celery(__name__)


def fetch_kpis():
    conn = get_db()
    pending_orders = conn.execute(
        text('SELECT COUNT(*) FROM orders WHERE status = :status'),
        {'status': 'pending'}
    ).fetchone()[0]
    pending_maintenance = conn.execute(
        text('SELECT COUNT(*) FROM maintenance WHERE status = :status'),
        {'status': 'pending'}
    ).fetchone()[0]
    expired_tenders = conn.execute(
        text("SELECT COUNT(*) FROM tenders WHERE status = 'expired'")
    ).fetchone()[0]
    monthly_sales = conn.execute(
        text(
            "SELECT COALESCE(SUM(total_sales),0) FROM kpi_sales WHERE month = DATE_TRUNC('month', CURRENT_DATE)"
        )
    ).fetchone()[0]
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
        'send-approval-reminders': {
            'task': 'analytics.send_approval_reminders',
            'schedule': crontab(hour=9, minute=0),
        },
        'forecast-sales': {
            'task': 'analytics.forecast_sales',
            'schedule': crontab(hour=2, minute=0, day_of_month='1'),
        },
        'monthly-compliance-report': {
            'task': 'analytics.generate_compliance_report',
            'schedule': crontab(hour=3, minute=0, day_of_month='1'),
        },
    }


@bp.route('/analytics/dashboard')
@login_required
@roles_required('Management')
def dashboard():
    kpis = fetch_kpis()
    forecast = forecast_sales()
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
        sales_forecast=forecast,
    )


@bp.route('/analytics/report-builder', methods=['GET', 'POST'])
@login_required
@roles_required('Management')
def report_builder():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        if report_type == 'compliance':
            generate_compliance_report.delay()
        else:
            build_custom_report.delay(report_type)
        flash('Report generation scheduled.')
        return redirect(url_for('analytics.report_builder'))
    return render_template('analytics/report_builder.html')


@socketio.on('connect')
def push_kpis():
    emit('kpi_update', fetch_kpis())


@celery.task
def generate_report():
    conn = get_db()
    orders = conn.execute(text('SELECT status, COUNT(*) FROM orders GROUP BY status')).fetchall()
    maintenance = conn.execute(text('SELECT status, COUNT(*) FROM maintenance GROUP BY status')).fetchall()
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
        text("UPDATE tenders SET status = 'expired' WHERE due_date < CURRENT_DATE AND status IS NULL")
    )
    conn.commit()
    conn.close()


@celery.task
def refresh_kpis():
    conn = get_db()
    try:
        conn.execute(text('REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_sales'))
        conn.commit()
    finally:
        conn.close()
    socketio.emit('kpi_update', fetch_kpis())


@celery.task
def send_approval_reminders():
    conn = get_db()
    pending = conn.execute(
        text('SELECT id FROM orders WHERE status = :status'), {'status': 'pending'}
    ).fetchall()
    conn.close()
    for order_id, in pending:
        message = f'Order {order_id} pending approval'
        print(f'Reminder: {message}')
        log_audit(None, None, 'reminder', message)
    return len(pending)


@celery.task
def forecast_sales(months: int = 3):
    conn = get_db()
    rows = conn.execute(
        text('SELECT total_sales FROM kpi_sales ORDER BY month DESC LIMIT :limit'),
        {'limit': months}
    ).fetchall()
    conn.close()
    values = [r[0] for r in rows]
    if not values:
        return 0.0
    return float(sum(values) / len(values))


@celery.task
def generate_compliance_report():
    conn = get_db()
    rows = conn.execute(
        text('SELECT id, status FROM orders WHERE status = :status'),
        {'status': 'pending'}
    ).fetchall()
    filename = f"compliance_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, 'w') as f:
        f.write('order_id,status\n')
        for oid, status in rows:
            f.write(f"{oid},{status}\n")
    conn.close()
    return filename


@celery.task
def build_custom_report(report_type: str):
    conn = get_db()
    if report_type == 'orders':
        rows = conn.execute(text('SELECT id, status FROM orders')).fetchall()
    elif report_type == 'maintenance':
        rows = conn.execute(text('SELECT id, status FROM maintenance')).fetchall()
    else:
        rows = []
    filename = f"{report_type}_report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, 'w') as f:
        for row in rows:
            f.write(','.join(str(col) for col in row) + '\n')
    conn.close()
    return filename
