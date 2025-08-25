from flask import Blueprint, render_template, redirect, url_for, session
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import DataRequired

from db import get_db
from erp.utils import login_required, roles_required
from erp.audit import log_audit
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
        'send-order-reminders': {
            'task': 'analytics.send_order_reminders',
            'schedule': crontab(hour=8, minute=0),
        },
        'monthly-compliance-report': {
            'task': 'analytics.generate_compliance_report',
            'schedule': crontab(day_of_month=1, hour=2, minute=0),
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


class ReportForm(FlaskForm):
    start = DateField('Start Date', validators=[DataRequired()])
    end = DateField('End Date', validators=[DataRequired()])
    report_type = SelectField(
        'Report Type',
        choices=[('visits', 'Field Reports')],
        validators=[DataRequired()],
    )
    submit = SubmitField('Generate')


@bp.route('/analytics/report-builder', methods=['GET', 'POST'])
@login_required
@roles_required('Management')
def report_builder():
    form = ReportForm()
    filename = None
    if form.validate_on_submit():
        filename = build_report(
            form.start.data.isoformat(),
            form.end.data.isoformat(),
            form.report_type.data,
        )
    return render_template('analytics/report_builder.html', form=form, filename=filename)


@bp.route('/analytics/forecast')
@login_required
@roles_required('Management')
def forecast():
    prediction = forecast_sales()
    return render_template('analytics/forecast.html', prediction=prediction)


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
def send_order_reminders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM orders WHERE status = 'pending'")
    order_ids = [row[0] for row in cur.fetchall()]
    for oid in order_ids:
        log_audit(None, None, 'reminder', f'Order {oid} pending approval')
    cur.close()
    conn.close()
    return order_ids


@celery.task
def build_report(start_date, end_date, report_type):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'SELECT institution, visit_date, sales_rep FROM reports WHERE visit_date BETWEEN ? AND ?',
        (start_date, end_date),
    )
    rows = cur.fetchall()
    filename = f"{report_type}_report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, 'w') as f:
        f.write('institution,visit_date,sales_rep\n')
        for inst, date, rep in rows:
            f.write(f"{inst},{date},{rep}\n")
    cur.close()
    conn.close()
    return filename


@celery.task
def forecast_sales():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT month, total_sales FROM kpi_sales ORDER BY month')
    data = [(datetime.fromisoformat(row[0]), float(row[1])) for row in cur.fetchall()]
    cur.close()
    conn.close()
    if len(data) < 2:
        return 0
    values = [row[1] for row in data]
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    avg_growth = sum(diffs) / len(diffs)
    return max(0, values[-1] + avg_growth)


@celery.task
def generate_compliance_report():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT customer, SUM(quantity) FROM orders GROUP BY customer')
    rows = cur.fetchall()
    filename = f"compliance_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, 'w') as f:
        f.write('customer,total_quantity\n')
        for cust, total in rows:
            f.write(f"{cust},{total}\n")
    cur.close()
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
