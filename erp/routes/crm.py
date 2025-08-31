from flask import (
    Blueprint,
    render_template,
    session,
    request,
    redirect,
    url_for,
    send_file,
    Response,
    stream_with_context,
    current_app,
    jsonify,
)
from db import get_db
from erp.workflow import require_enabled
from io import BytesIO, StringIO
import csv
from openpyxl import Workbook
from sqlalchemy import text

bp = Blueprint("crm", __name__, url_prefix="/crm")

ALLOWED_SORTS = {"id", "name"}


def _sanitize_sort(sort: str) -> str:
    return sort if sort in ALLOWED_SORTS else "id"


def _sanitize_direction(direction: str) -> str:
    return direction if direction in {"asc", "desc"} else "asc"


@bp.route("/")
@require_enabled("crm")
def index():
    org_id = session.get("org_id")
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    sort = _sanitize_sort(request.args.get("sort", "id"))
    direction = _sanitize_direction(request.args.get("dir", "asc"))
    sort_col = sort
    order_sql = "DESC" if direction == "desc" else "ASC"
    conn = get_db()
    cur = conn.execute(
        text(
            f"SELECT id, name FROM crm_customers WHERE org_id = :org ORDER BY {sort_col} {order_sql} LIMIT :limit OFFSET :offset"
        ),
        {"org": org_id, "limit": limit, "offset": offset},
    )
    customers = cur.fetchall()
    cur.close()
    conn.close()
    next_offset = offset + limit if len(customers) == limit else None
    prev_offset = offset - limit if offset - limit >= 0 else None
    if current_app.config.get("TESTING"):
        return jsonify([{"id": c[0], "name": c[1]} for c in customers])
    return render_template(
        "crm/index.html",
        customers=customers,
        sort=sort,
        direction=direction,
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


@bp.route("/import", methods=["GET", "POST"])
@require_enabled("crm")
def import_customers():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename:
            stream = StringIO(file.stream.read().decode("utf-8"))
            reader = csv.reader(stream)
            next(reader, None)
            conn = get_db()
            cur = conn.cursor()
            org_id = session.get("org_id")
            for row in reader:
                if row:
                    cur.execute(
                        "INSERT INTO crm_customers (org_id, name) VALUES (%s, %s)",
                        (org_id, row[0]),
                    )
            conn.commit()
            cur.close()
            conn.close()
        return redirect(url_for("crm.index"))
    return render_template("crm/import.html")


def _export_customers(org_id: int, sort: str, direction: str, fmt: str):
    sort = _sanitize_sort(sort)
    direction = _sanitize_direction(direction)
    order_sql = "DESC" if direction == "desc" else "ASC"
    conn = get_db()
    cur = conn.execute(
        text(
            f"SELECT id, name FROM crm_customers WHERE org_id = :org ORDER BY {sort} {order_sql}"
        ),
        {"org": org_id},
    )
    headers = ["id", "name"]
    if fmt == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for r in cur:
            ws.append(list(r))
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        cur.close()
        conn.close()
        return send_file(
            bio,
            as_attachment=True,
            download_name="clients.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def generate():
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow(headers)
        yield sio.getvalue()
        sio.seek(0)
        sio.truncate(0)
        for r in cur:
            writer.writerow(list(r))
            yield sio.getvalue()
            sio.seek(0)
            sio.truncate(0)
        cur.close()
        conn.close()

    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients.csv"},
    )


@bp.route("/export.csv")
@require_enabled("crm")
def export_customers_csv():
    org_id = session.get("org_id")
    sort = request.args.get("sort", "id")
    direction = request.args.get("dir", "asc")
    return _export_customers(org_id, sort, direction, "csv")


@bp.route("/export.xlsx")
@require_enabled("crm")
def export_customers_xlsx():
    org_id = session.get("org_id")
    sort = request.args.get("sort", "id")
    direction = request.args.get("dir", "asc")
    return _export_customers(org_id, sort, direction, "xlsx")
