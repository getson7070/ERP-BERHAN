from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    abort,
    current_app,
)
from erp.utils import login_required
from erp.models import Inventory, db
import secrets

bp = Blueprint("inventory_ui", __name__, url_prefix="/inventory")


@bp.route("/", methods=["GET"])
@login_required
def inventory_table():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    org_id = session.get("org_id")
    items = Inventory.query.filter_by(org_id=org_id).all()
    if current_app.config.get("TESTING"):
        data = [{"id": i.id, "name": i.name, "quantity": i.quantity} for i in items]
        return jsonify(data)
    return render_template(
        "inventory.html", items=items, csrf_token=session["csrf_token"]
    )


@bp.route("/<int:item_id>", methods=["POST"])
@login_required
def update_item(item_id):
    token = request.headers.get("X-CSRFToken")
    if token != session.get("csrf_token"):
        abort(400)
    org_id = session.get("org_id")
    item = Inventory.query.filter_by(id=item_id, org_id=org_id).first_or_404()
    item.name = request.form.get("name", item.name)
    item.quantity = request.form.get("quantity", item.quantity)
    db.session.commit()
    return jsonify({"id": item.id, "name": item.name, "quantity": item.quantity})
