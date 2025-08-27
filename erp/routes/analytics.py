from flask import Blueprint, render_template, redirect, url_for, session, Response
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, UTC
from flask import request

# Forecasting uses simple averages; avoid heavy ML deps for lightweight installs

from db import get_db
from erp.utils import login_required, roles_required, task_idempotent
from erp import socketio
from flask_socketio import emit

bp = Blueprint('analytics', __name__)

celery = Celery(__name__)


def fetch_kpis():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM orders WHERE status = %s', ('pending',))
    pending_orders = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM maintenance WHERE status = %s', ('pending',))
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
        'send-approval-reminders': {
            'task': 'analytics.send_approval_reminders',
            'schedule': crontab(hour='*/4'),
        },
        'forecast-monthly-sales': {
            'task': 'analytics.forecast_sales',
            'schedule': crontab(hour=2, minute=0, day_of_month='1'),
        },
        'weekly-compliance-report': {
            'task': 'analytics.generate_compliance_report',
            'schedule': crontab(hour=3, minute=0, day_of_week='sun'),
        },
        'dedupe-crm-customers': {
            'task': 'analytics.deduplicate_customers',
            'schedule': crontab(hour=4, minute=0),
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
    filename = f"report_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.csv"
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


@celery.task
@task_idempotent
def send_approval_reminders(idempotency_key=None):
    """Notify sales reps of orders awaiting approval."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, sales_rep FROM orders WHERE status = 'pending'")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for order_id, rep in rows:
        print(f'Reminder sent to {rep} for order {order_id}')
    return len(rows)


@celery.task
@task_idempotent
def forecast_sales(idempotency_key=None):
    """Naive monthly sales forecast using average trend."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT total_sales FROM kpi_sales ORDER BY month DESC LIMIT 2')
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    if len(rows) < 2:
        return 0.0
    trend = rows[0] - rows[1]
    return float(rows[0] + trend)


@celery.task
@task_idempotent
def generate_compliance_report(idempotency_key=None):
    """Produce a simple CSV listing orders missing status."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM orders WHERE status IS NULL")
    missing = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    filename = f"compliance_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, 'w') as f:
        f.write('order_id\n')
        for oid in missing:
            f.write(f"{oid}\n")
    return filename


@celery.task
def deduplicate_customers():
    from erp.data_quality import deduplicate
    return deduplicate('crm_customers', ['org_id','name'])
    

@bp.route('/analytics/reports', methods=['GET', 'POST'])
@login_required
@roles_required('Management')
def report_builder():
    """Simple tabular report builder supporting orders and tenders."""
    rows = []
    headers = []
    anomalies = []
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        conn = get_db(); cur = conn.cursor()
        if report_type == 'orders':
            cur.execute('SELECT id, customer, status FROM orders')
            headers = ['id', 'customer', 'status']
        else:
            cur.execute('SELECT id, title, status FROM tenders')
            headers = ['id', 'title', 'status']
        rows = cur.fetchall()
        anomalies = detect_anomalies([r[0] for r in rows])
        cur.close(); conn.close()
    return render_template('analytics/report_builder.html', rows=rows, headers=headers, anomalies=anomalies)

import io, csv, statistics
@bp.route('/analytics/reports/export/<fmt>', methods=['POST'])
@login_required
@roles_required('Management')
def export_report(fmt):
    report_type = request.form.get('report_type')
    conn = get_db(); cur = conn.cursor()
    if report_type == 'orders':
        cur.execute('SELECT id, customer, status FROM orders')
        headers = ['id','customer','status']
    else:
        cur.execute('SELECT id, title, status FROM tenders')
        headers = ['id','title','status']
    rows = cur.fetchall(); cur.close(); conn.close()
    if fmt == 'excel':
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append(list(r))
        out = io.BytesIO(); wb.save(out)
        data = out.getvalue()
        ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext = 'xlsx'
    else:
        from reportlab.platypus import SimpleDocTemplate, Table
        from reportlab.lib.pagesizes import letter
        out = io.BytesIO()
        doc = SimpleDocTemplate(out, pagesize=letter)
        doc.build([Table([headers, *rows])])
        data = out.getvalue()
        ct = 'application/pdf'
        ext = 'pdf'
    return Response(data, mimetype=ct, headers={'Content-Disposition': f'attachment; filename=report.{ext}'})

def detect_anomalies(values):
    if not values:
        return []
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values) or 1
    return [v for v in values if abs(v-mean) > 3*stdev]
