from flask import (
    Blueprint,
    render_template,
    session,
    request,
    redirect,
    url_for,
    make_response,
    send_file,
)
from db import get_db
from erp.workflow import require_enabled
from io import BytesIO, StringIO
import csv
from openpyxl import Workbook

bp = Blueprint("crm", __name__, url_prefix="/crm")


@bp.route("/")
@require_enabled("crm")
def index():
    org_id = session.get("org_id")
    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc")
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    columns = {"id": "id", "name": "name"}
    sort_col = columns.get(sort, "id")
    order_sql = "DESC" if order == "desc" else "ASC"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        f"SELECT id, name FROM crm_customers WHERE org_id = %s ORDER BY {sort_col} {order_sql} LIMIT %s OFFSET %s",
        (org_id, limit, offset),
    )
    customers = cur.fetchall()
    cur.close()
    conn.close()
    next_offset = offset + limit if len(customers) == limit else None
    prev_offset = offset - limit if offset - limit >= 0 else None
    return render_template(
        "crm/index.html",
        customers=customers,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
        next_offset=next_offset,
        prev_offset=prev_offset,
    )


@bp.route("/add", methods=["GET", "POST"])
@require_enabled("crm")
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        conn = get_db()
        cur = conn.cursor()
        org_id = session.get("org_id")
        cur.execute(
            "INSERT INTO crm_customers (org_id, name) VALUES (%s,%s)", (org_id, name)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("crm.index"))
    return render_template("crm/add.html")


@bp.route("/export")
@require_enabled("crm")
def export_customers():
    org_id = session.get("org_id")
    fmt = request.args.get("format", "csv")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name FROM crm_customers WHERE org_id = %s ORDER BY id",
        (org_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    headers = ["id", "name"]
    if fmt == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append(list(r))
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        return send_file(
            bio,
            as_attachment=True,
            download_name="clients.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    sio = StringIO()
    writer = csv.writer(sio)
    writer.writerow(headers)
    for r in rows:
        writer.writerow(list(r))
    resp = make_response(sio.getvalue())
    resp.headers["Content-Disposition"] = "attachment; filename=clients.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp
