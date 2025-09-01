from flask import (
    Blueprint,
    render_template,
    session,
    request,
    redirect,
    url_for,
    current_app,
    jsonify,
)
from sqlalchemy import text
from db import get_db
from erp.workflow import require_enabled
from erp.utils import sanitize_sort, sanitize_direction, stream_export

bp = Blueprint("crm", __name__, url_prefix="/crm")

ALLOWED_SORTS = {"id", "name"}


@bp.route("/")
@require_enabled("crm")
def index():
    org_id = session.get("org_id")
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    sort = sanitize_sort(request.args.get("sort", "id"), ALLOWED_SORTS, "id")
    direction = sanitize_direction(request.args.get("dir", "asc"))
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
        org_id = session.get("org_id")
        conn.execute(
            text("INSERT INTO crm_customers (org_id, name) VALUES (:org, :name)"),
            {"org": org_id, "name": name},
        )
        conn.commit()
        conn.close()
        return redirect(url_for("crm.index"))
    return render_template("crm/add.html")


@bp.route("/export.csv")
@require_enabled("crm")
def export_customers_csv():
    org_id = session.get("org_id")
    sort = request.args.get("sort", "id")
    direction = request.args.get("dir", "asc")
    sort = sanitize_sort(sort, ALLOWED_SORTS, "id")
    direction = sanitize_direction(direction)
    order_sql = "DESC" if direction == "desc" else "ASC"
    conn = get_db()
    cur = conn.execute(
        text(
            f"SELECT id, name FROM crm_customers WHERE org_id = :org ORDER BY {sort} {order_sql}"
        ),
        {"org": org_id},
    )
    headers = ["id", "name"]

    def rows():
        try:
            for r in cur:
                yield list(r)
        finally:
            cur.close()
            conn.close()

    return stream_export(rows(), headers, "clients", "csv")


@bp.route("/export.xlsx")
@require_enabled("crm")
def export_customers_xlsx():
    org_id = session.get("org_id")
    sort = request.args.get("sort", "id")
    direction = request.args.get("dir", "asc")
    sort = sanitize_sort(sort, ALLOWED_SORTS, "id")
    direction = sanitize_direction(direction)
    order_sql = "DESC" if direction == "desc" else "ASC"
    conn = get_db()
    cur = conn.execute(
        text(
            f"SELECT id, name FROM crm_customers WHERE org_id = :org ORDER BY {sort} {order_sql}"
        ),
        {"org": org_id},
    )
    headers = ["id", "name"]

    def rows():
        try:
            for r in cur:
                yield list(r)
        finally:
            cur.close()
            conn.close()

    return stream_export(rows(), headers, "clients", "xlsx")
