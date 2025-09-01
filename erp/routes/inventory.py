from flask import Blueprint, render_template, request, jsonify, session, current_app
from erp.utils import login_required, sanitize_sort, sanitize_direction, stream_export
from erp.models import Inventory, db

bp = Blueprint("inventory_ui", __name__, url_prefix="/inventory")

ALLOWED_SORTS = {"id", "sku", "name", "quantity"}


def _build_query(org_id, sku, sort, direction):
    query = Inventory.query.filter_by(org_id=org_id)
    if sku:
        query = query.filter_by(sku=sku)
    sort = sanitize_sort(sort, ALLOWED_SORTS, "id")
    direction = sanitize_direction(direction)
    sort_attr = getattr(Inventory, sort)
    sort_attr = sort_attr.desc() if direction == "desc" else sort_attr.asc()
    return query.order_by(sort_attr)


@bp.route("/", methods=["GET"])
@login_required
def inventory_table():
    org_id = session.get("org_id")
    sku = request.args.get("sku")
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    sort = sanitize_sort(request.args.get("sort", "id"), ALLOWED_SORTS, "id")
    direction = sanitize_direction(request.args.get("dir", "asc"))
    query = _build_query(org_id, sku, sort, direction)
    items = query.offset(offset).limit(limit).all()
    next_offset = offset + limit if len(items) == limit else None
    prev_offset = offset - limit if offset - limit >= 0 else None
    if current_app.config.get("TESTING"):
        data = [
            {"id": i.id, "name": i.name, "sku": i.sku, "quantity": i.quantity}
            for i in items
        ]
        return jsonify(data)
    return render_template(
        "inventory/index.html",
        items=items,
        next_offset=next_offset,
        prev_offset=prev_offset,
        limit=limit,
        sku=sku,
        offset=offset,
        sort=sort,
        direction=direction,
    )


@bp.route("/<int:item_id>", methods=["POST"])
@login_required
def update_item(item_id):
    org_id = session.get("org_id")
    item = Inventory.query.filter_by(id=item_id, org_id=org_id).first_or_404()
    item.name = request.form.get("name", item.name)
    item.sku = request.form.get("sku", item.sku)
    item.quantity = request.form.get("quantity", item.quantity)
    db.session.commit()
    return jsonify(
        {"id": item.id, "name": item.name, "sku": item.sku, "quantity": item.quantity}
    )




@bp.route("/export.csv")
@login_required
def export_inventory_csv():
    org_id = session.get("org_id")
    sku = request.args.get("sku")
    sort = sanitize_sort(request.args.get("sort", "id"), ALLOWED_SORTS, "id")
    direction = sanitize_direction(request.args.get("dir", "asc"))
    query = _build_query(org_id, sku, sort, direction)
    headers = ["id", "sku", "name", "quantity"]
    rows = ([i.id, i.sku, i.name, i.quantity] for i in query)
    return stream_export(rows, headers, "inventory", "csv")


@bp.route("/export.xlsx")
@login_required
def export_inventory_xlsx():
    org_id = session.get("org_id")
    sku = request.args.get("sku")
    sort = sanitize_sort(request.args.get("sort", "id"), ALLOWED_SORTS, "id")
    direction = sanitize_direction(request.args.get("dir", "asc"))
    query = _build_query(org_id, sku, sort, direction)
    headers = ["id", "sku", "name", "quantity"]
    rows = ([i.id, i.sku, i.name, i.quantity] for i in query)
    return stream_export(rows, headers, "inventory", "xlsx")
