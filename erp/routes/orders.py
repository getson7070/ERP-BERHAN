from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    make_response,
    send_file,
)
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, NumberRange

from sqlalchemy import text
from io import BytesIO, StringIO
import csv
from openpyxl import Workbook
from db import get_db
from erp.utils import login_required, has_permission, idempotency_key_required

bp = Blueprint("orders", __name__)


@bp.route("/put_order", methods=["GET", "POST"])
@login_required
@idempotency_key_required
def put_order():
    if not has_permission("put_order"):
        return redirect(url_for("main.dashboard"))

    class OrderForm(FlaskForm):
        item_id = SelectField("Item", coerce=int, validators=[DataRequired()])
        quantity = IntegerField(
            "Quantity", validators=[DataRequired(), NumberRange(min=1)]
        )
        customer = StringField("Customer", validators=[DataRequired()])
        vat_exempt = BooleanField("VAT Exempt")
        submit = SubmitField("Submit Order")

    conn = get_db()
    cur = conn.execute(text("SELECT id, item_code FROM inventory"))
    form = OrderForm()
    form.item_id.choices = [(row[0], row[1]) for row in cur.fetchall()]
    if form.validate_on_submit():
        item_id = form.item_id.data
        quantity = form.quantity.data
        customer = form.customer.data
        vat_exempt = form.vat_exempt.data
        user = (
            session.get("username")
            if session.get("role") != "Client"
            else session["tin"]
        )
        conn.execute(
            text(
                "INSERT INTO orders (item_id, quantity, customer, sales_rep, vat_exempt, status) "
                "VALUES (:item_id, :quantity, :customer, :sales_rep, :vat_exempt, 'pending')"
            ),
            {
                "item_id": item_id,
                "quantity": quantity,
                "customer": customer,
                "sales_rep": user,
                "vat_exempt": vat_exempt,
            },
        )
        conn.commit()
        conn.close()
        return redirect(url_for("main.dashboard"))
    conn.close()
    return render_template("put_order.html", form=form)


@bp.route("/orders")
@login_required
def orders():
    if not has_permission("view_orders"):
        return redirect(url_for("main.dashboard"))
    conn = get_db()
    pending_orders = conn.execute(
        text("SELECT * FROM orders WHERE status = 'pending' ORDER BY id DESC LIMIT 5")
    ).fetchall()
    approved_orders = conn.execute(
        text("SELECT * FROM orders WHERE status = 'approved' ORDER BY id DESC LIMIT 5")
    ).fetchall()
    rejected_orders = conn.execute(
        text("SELECT * FROM orders WHERE status = 'rejected' ORDER BY id DESC LIMIT 5")
    ).fetchall()
    conn.close()
    return render_template(
        "orders.html",
        pending_orders=pending_orders,
        approved_orders=approved_orders,
        rejected_orders=rejected_orders,
    )


@bp.route("/list")
@login_required
def orders_list():
    if not has_permission("view_orders"):
        return redirect(url_for("main.dashboard"))
    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc")
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    columns = {
        "id": "id",
        "item_id": "item_id",
        "quantity": "quantity",
        "customer": "customer",
        "status": "status",
    }
    sort_col = columns.get(sort, "id")
    order_sql = "DESC" if order == "desc" else "ASC"
    conn = get_db()
    rows = (
        conn.execute(
            text(
                f"SELECT id, item_id, quantity, customer, status FROM orders ORDER BY {sort_col} {order_sql} LIMIT :limit OFFSET :offset"
            ),
            {"limit": limit, "offset": offset},
        )
        .mappings()
        .fetchall()
    )
    conn.close()
    next_offset = offset + limit if len(rows) == limit else None
    prev_offset = offset - limit if offset - limit >= 0 else None
    return render_template(
        "orders_list.html",
        orders=rows,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
        next_offset=next_offset,
        prev_offset=prev_offset,
    )


@bp.route("/export")
@login_required
def export_orders():
    if not has_permission("view_orders"):
        return redirect(url_for("main.dashboard"))
    fmt = request.args.get("format", "csv")
    conn = get_db()
    rows = (
        conn.execute(
            text(
                "SELECT id, item_id, quantity, customer, status FROM orders ORDER BY id"
            )
        )
        .mappings()
        .fetchall()
    )
    conn.close()
    headers = ["id", "item_id", "quantity", "customer", "status"]
    if fmt == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append([r[h] for h in headers])
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        return send_file(
            bio,
            as_attachment=True,
            download_name="orders.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    sio = StringIO()
    writer = csv.writer(sio)
    writer.writerow(headers)
    for r in rows:
        writer.writerow([r[h] for h in headers])
    resp = make_response(sio.getvalue())
    resp.headers["Content-Disposition"] = "attachment; filename=orders.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp
