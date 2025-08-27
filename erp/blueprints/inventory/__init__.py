"""Inventory blueprint providing basic CRUD routes."""

from flask import Blueprint, request, jsonify, current_app, session, abort

from erp.models import Inventory, db

bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@bp.route("/", methods=["GET"])
def list_items():
    """Return inventory items for the current organisation."""
    org_id = session.get("org_id")
    if org_id is None:
        abort(401)
    items = Inventory.query.filter_by(org_id=org_id).all()
    data = [
        {"id": i.id, "name": i.name, "quantity": i.quantity} for i in items
    ]
    if current_app.config.get("TESTING"):
        return jsonify(data)
    return jsonify(data)


@bp.route("/", methods=["POST"])
def create_item():
    payload = request.get_json() or {}
    item = Inventory(
        org_id=session.get("org_id"),
        name=payload.get("name", ""),
        quantity=payload.get("quantity", 0),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"id": item.id, "name": item.name, "quantity": item.quantity}), 201


@bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    return jsonify({"id": item.id, "name": item.name, "quantity": item.quantity})


@bp.route("/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    payload = request.get_json() or {}
    item.name = payload.get("name", item.name)
    item.quantity = payload.get("quantity", item.quantity)
    db.session.commit()
    return jsonify({"id": item.id, "name": item.name, "quantity": item.quantity})


@bp.route("/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204
