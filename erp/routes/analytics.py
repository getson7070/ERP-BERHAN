import io
import os
import statistics
from datetime import datetime, UTC

from celery import Celery
from celery.schedules import crontab
from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    session,
    current_app,
)
from flask_socketio import emit
from sqlalchemy import create_engine, text

# Forecasting uses simple averages to avoid heavy ML dependencies.

from db import get_db
from erp import socketio, KPI_SALES_MV_AGE
from erp.utils import login_required, roles_required, task_idempotent

bp = Blueprint("analytics", __name__)

celery = Celery(__name__)


def fetch_kpis(org_id: int | None = None):
    conn = get_db()
    if org_id is not None:
        pending_orders = conn.execute(
            text(
                "SELECT COUNT(*) FROM orders WHERE status = :status AND org_id = :org"
            ),
            {"status": "pending", "org": org_id},
        ).scalar()
        pending_maintenance = conn.execute(
            text(
                "SELECT COUNT(*) FROM maintenance WHERE status = :status AND org_id = :org"
            ),
            {"status": "pending", "org": org_id},
        ).scalar()
        expired_tenders = conn.execute(
            text(
                "SELECT COUNT(*) FROM tenders WHERE status = :status AND org_id = :org"
            ),
            {"status": "expired", "org": org_id},
        ).scalar()
    else:
        pending_orders = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE status = :status"),
            {"status": "pending"},
        ).scalar()
        pending_maintenance = conn.execute(
            text("SELECT COUNT(*) FROM maintenance WHERE status = :status"),
            {"status": "pending"},
        ).scalar()
        expired_tenders = conn.execute(
            text("SELECT COUNT(*) FROM tenders WHERE status = :status"),
            {"status": "expired"},
        ).scalar()
    monthly_sales = conn.execute(
        text(
            "SELECT COALESCE(SUM(total_sales),0) FROM kpi_sales "
            "WHERE month = DATE_TRUNC('month', CURRENT_DATE)"
        )
    ).scalar()
    conn.close()
    return {
        "pending_orders": pending_orders or 0,
        "pending_maintenance": pending_maintenance or 0,
        "expired_tenders": expired_tenders or 0,
        "monthly_sales": float(monthly_sales or 0),
    }


@bp.record_once
def init_celery(state):
    app = state.app
    celery.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery.conf.result_backend = app.config["CELERY_RESULT_BACKEND"]
    celery.conf.update(app.config)
    celery.conf.imports = ["erp.data_retention", "backup"]

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    celery.conf.beat_schedule = {
        "generate-daily-report": {
            "task": "analytics.generate_report",
            "schedule": crontab(hour=0, minute=0),
        },
        "expire-due-tenders": {
            "task": "analytics.expire_tenders",
            "schedule": crontab(hour=1, minute=0),
        },
        "refresh-kpi-sales": {
            "task": "analytics.refresh_kpis",
            "schedule": crontab(minute="*/5"),
        },
        "check-kpi-staleness": {
            "task": "analytics.check_kpi_staleness",
            "schedule": crontab(minute="*/5"),
        },
        "export-kpi-olap": {
            "task": "analytics.export_kpis_to_olap",
            "schedule": crontab(hour=2, minute=0),
        },
        "send-approval-reminders": {
            "task": "analytics.send_approval_reminders",
            "schedule": crontab(hour="*/4"),
        },
        "forecast-monthly-sales": {
            "task": "analytics.forecast_sales",
            "schedule": crontab(hour=2, minute=0, day_of_month="1"),
        },
        "weekly-compliance-report": {
            "task": "analytics.generate_compliance_report",
            "schedule": crontab(hour=3, minute=0, day_of_week="sun"),
        },
        "dedupe-crm-customers": {
            "task": "analytics.deduplicate_customers",
            "schedule": crontab(hour=4, minute=0),
        },
        "purge-expired-rows": {
            "task": "data_retention.purge_expired_rows",
            "schedule": crontab(hour=3, minute=30),
        },
        "anonymize-users": {
            "task": "data_retention.anonymize_users",
            "schedule": crontab(hour=3, minute=45),
        },
        "quarterly-access-recert": {
            "task": "data_retention.run_access_recert_export",
            "schedule": crontab(
                month_of_year="1,4,7,10", day_of_month=1, hour=5, minute=0
            ),
        },
        "nightly-db-backup": {
            "task": "backup.run_backup",
            "schedule": crontab(hour=2, minute=30),
        },
        "monthly-restore-drill": {
            "task": "backup.run_restore_drill",
            "schedule": crontab(day_of_month=1, hour=3, minute=0),
        },
    }


@bp.route("/analytics/dashboard")
@login_required
def dashboard():
    kpis = fetch_kpis(session.get("org_id"))
    role = session.get("role")
    permissions = session.get("permissions", [])
    conn = get_db()
    cur = conn.execute(
        text(
            "SELECT r.name FROM role_assignments ra JOIN roles r ON ra.role_id = r.id "
            "WHERE ra.user_id = :uid AND ra.org_id = :org"
        ),
        {"uid": session.get("user_id"), "org": session.get("org_id")},
    )
    roles = [row[0] for row in cur.fetchall()]
    saved_cur = conn.execute(
        text("SELECT name, query FROM saved_searches WHERE user_id = :uid"),
        {"uid": session.get("user_id")},
    )
    saved_searches = saved_cur.fetchall()
    audit_logs: list[str] = []
    if "Auditor" in roles:
        log_cur = conn.execute(
            text(
                "SELECT action FROM audit_logs WHERE org_id = :org "
                "ORDER BY created_at DESC LIMIT 5"
            ),
            {"org": session.get("org_id")},
        )
        audit_logs = [row[0] for row in log_cur.fetchall()]
    conn.close()
    return render_template(
        "analytics/dashboard.html",
        role=role,
        permissions=permissions,
        roles=roles,
        audit_logs=audit_logs,
        saved_searches=saved_searches,
        pending_orders=kpis["pending_orders"],
        pending_maintenance=kpis["pending_maintenance"],
        expired_tenders=kpis["expired_tenders"],
        monthly_sales=kpis["monthly_sales"],
    )


@socketio.on("connect")
def push_kpis():
    emit("kpi_update", fetch_kpis(session.get("org_id")))


@celery.task
@task_idempotent
def generate_report(idempotency_key=None):
    conn = get_db()
    orders = conn.execute(
        text("SELECT status, COUNT(*) FROM orders GROUP BY status")
    ).fetchall()
    maintenance = conn.execute(
        text("SELECT status, COUNT(*) FROM maintenance GROUP BY status")
    ).fetchall()
    filename = f"report_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, "w") as f:
        f.write("Orders\n")
        for status, count in orders:
            f.write(f"{status},{count}\n")
        f.write("Maintenance\n")
        for status, count in maintenance:
            f.write(f"{status},{count}\n")
    conn.close()
    return filename


@celery.task
@task_idempotent
def expire_tenders(idempotency_key=None):
    conn = get_db()
    conn.execute(
        text(
            "UPDATE tenders SET status = 'expired' "
            "WHERE due_date < CURRENT_DATE AND status IS NULL"
        )
    )
    conn.commit()
    conn.close()


@celery.task
@task_idempotent
def refresh_kpis(idempotency_key=None):
    conn = get_db()
    dialect = conn._dialect.name
    conn.execute(text("CREATE TABLE IF NOT EXISTS kpi_refresh_log (last_refresh TEXT)"))
    last_refresh = conn.execute(
        text(
            "SELECT COALESCE(MAX(last_refresh), '1970-01-01T00:00:00') FROM kpi_refresh_log"
        )
    ).fetchone()[0]
    if dialect == "sqlite":
        sales_sql = text(
            """
            INSERT INTO kpi_sales (month, total_sales)
            SELECT strftime('%Y-%m-01', order_date) AS month, SUM(total_amount) AS total_sales
            FROM orders
            WHERE order_date >= :last_refresh
            GROUP BY 1
            ON CONFLICT (month) DO UPDATE SET total_sales = excluded.total_sales
            """
        )
    else:
        sales_sql = text(
            """
            INSERT INTO kpi_sales (month, total_sales)
            SELECT DATE_TRUNC('month', order_date) AS month, SUM(total_amount) AS total_sales
            FROM orders
            WHERE order_date >= :last_refresh
            GROUP BY 1
            ON CONFLICT (month) DO UPDATE SET total_sales = excluded.total_sales
            """
        )
    conn.execute(sales_sql, {"last_refresh": last_refresh})
    new_last = (
        conn.execute(text("SELECT MAX(order_date) FROM orders")).fetchone()[0]
        or last_refresh
    )
    conn.execute(
        text("INSERT INTO kpi_refresh_log (last_refresh) VALUES (:last_refresh)"),
        {"last_refresh": new_last},
    )
    conn.commit()
    conn.close()
    socketio.emit("kpi_update", fetch_kpis())
    kpi_staleness_seconds()


def kpi_staleness_seconds() -> float:
    """Return age of the kpi_sales dataset in seconds and update gauge."""
    conn = get_db()
    conn.execute(text("CREATE TABLE IF NOT EXISTS kpi_refresh_log (last_refresh TEXT)"))
    row = conn.execute(text("SELECT MAX(last_refresh) FROM kpi_refresh_log")).fetchone()
    conn.close()
    if not row or row[0] is None:
        age = 0.0
    else:
        last = row[0]
        if isinstance(last, str):
            last_dt = datetime.fromisoformat(last)
        else:
            last_dt = last
        age = (datetime.now(UTC) - last_dt).total_seconds()
    KPI_SALES_MV_AGE.set(age)
    return age


@celery.task
def check_kpi_staleness():
    age = kpi_staleness_seconds()
    if age > 600:
        current_app.logger.warning("kpi_sales MV staleness %.0fs", age)
        socketio.emit(
            "alert",
            {"metric": "kpi_sales_mv_age_seconds", "age": age},
        )


@celery.task
@task_idempotent
def export_kpis_to_olap(idempotency_key=None):
    dsn = os.environ.get("OLAP_DSN")
    if not dsn:
        return 0
    src = get_db()
    rows = src.execute(text("SELECT month, total_sales FROM kpi_sales")).fetchall()
    src.close()
    engine = create_engine(dsn)
    inserted = 0
    with engine.begin() as conn:
        for month, total in rows:
            conn.execute(
                text("INSERT INTO kpi_sales (month, total_sales) " "VALUES (:m, :t)"),
                {"m": month, "t": total},
            )
            inserted += 1
    return inserted


@celery.task
@task_idempotent
def send_approval_reminders(idempotency_key=None):
    """Notify sales reps of orders awaiting approval."""
    conn = get_db()
    rows = conn.execute(
        text("SELECT id, sales_rep FROM orders WHERE status = :status"),
        {"status": "pending"},
    ).fetchall()
    conn.close()
    for order_id, rep in rows:
        print(f"Reminder sent to {rep} for order {order_id}")
    return len(rows)


@celery.task
@task_idempotent
def forecast_sales(idempotency_key=None):
    """Naive monthly sales forecast using average trend."""
    conn = get_db()
    rows = [
        r[0]
        for r in conn.execute(
            text("SELECT total_sales FROM kpi_sales ORDER BY month DESC LIMIT 2")
        ).fetchall()
    ]
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
    rows = conn.execute(text("SELECT id FROM orders WHERE status IS NULL")).fetchall()
    conn.close()
    missing = [r[0] for r in rows]
    filename = f"compliance_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.csv"
    with open(filename, "w") as f:
        f.write("order_id\n")
        for oid in missing:
            f.write(f"{oid}\n")
    return filename


@celery.task
@task_idempotent
def deduplicate_customers(idempotency_key=None):
    from erp.data_quality import deduplicate

    return deduplicate("crm_customers", ["org_id", "name"])


@bp.route("/analytics/reports", methods=["GET", "POST"])
@login_required
@roles_required("Management")
def report_builder():
    """Simple tabular report builder supporting orders and tenders."""
    rows = []
    headers = []
    anomalies = []
    if request.method == "POST":
        report_type = request.form.get("report_type")
        conn = get_db()
        if report_type == "orders":
            rows = conn.execute(
                text("SELECT id, customer, status FROM orders WHERE org_id = :org"),
                {"org": session.get("org_id")},
            ).fetchall()
            headers = ["id", "customer", "status"]
        else:
            rows = conn.execute(
                text("SELECT id, title, status FROM tenders WHERE org_id = :org"),
                {"org": session.get("org_id")},
            ).fetchall()
            headers = ["id", "title", "status"]
        anomalies = detect_anomalies([r[0] for r in rows])
        conn.close()
    return render_template(
        "analytics/report_builder.html",
        rows=rows,
        headers=headers,
        anomalies=anomalies,
    )


@bp.route("/analytics/reports/export/<fmt>", methods=["POST"])
@login_required
@roles_required("Management")
def export_report(fmt):
    report_type = request.form.get("report_type")
    conn = get_db()
    if report_type == "orders":
        rows = conn.execute(
            text("SELECT id, customer, status FROM orders WHERE org_id = :org"),
            {"org": session.get("org_id")},
        ).fetchall()
        headers = ["id", "customer", "status"]
    else:
        rows = conn.execute(
            text("SELECT id, title, status FROM tenders WHERE org_id = :org"),
            {"org": session.get("org_id")},
        ).fetchall()
        headers = ["id", "title", "status"]
    conn.close()
    if fmt == "excel":
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append(list(r))
        out = io.BytesIO()
        wb.save(out)
        data = out.getvalue()
        ct = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    else:
        from reportlab.platypus import SimpleDocTemplate, Table
        from reportlab.lib.pagesizes import letter

        out = io.BytesIO()
        doc = SimpleDocTemplate(out, pagesize=letter)
        doc.build([Table([headers, *rows])])
        data = out.getvalue()
        ct = "application/pdf"
        ext = "pdf"
    return Response(
        data,
        mimetype=ct,
        headers={"Content-Disposition": f"attachment; filename=report.{ext}"},
    )


def detect_anomalies(values):
    if not values:
        return []
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values) or 1
    return [v for v in values if abs(v - mean) > 3 * stdev]
