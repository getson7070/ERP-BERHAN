"""Inventory blueprint providing basic CRUD routes."""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from flask_security import roles_required, roles_accepted

from erp.models import Inventory, db

bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@bp.route("/", methods=["GET"])
@jwt_required()
@roles_accepted("admin", "pharmacist")
def list_items():
    """Return inventory items for the current organisation."""
    org_id = get_jwt().get("org_id")
    items = Inventory.query.filter_by(org_id=org_id).all()
    data = [
        {"id": i.id, "name": i.name, "quantity": i.quantity} for i in items
    ]
    if current_app.config.get("TESTING"):
        return jsonify(data)
    return jsonify(data)


@bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("pharmacist")
def create_item():
    payload = request.get_json() or {}
    claims = get_jwt()
    item = Inventory(
        org_id=claims.get("org_id"),
        name=payload.get("name", ""),
        quantity=payload.get("quantity", 0),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"id": item.id, "name": item.name, "quantity": item.quantity}), 201


@bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
@roles_accepted("admin", "pharmacist")
def get_item(item_id):
    org_id = get_jwt().get("org_id")
    item = Inventory.query.filter_by(id=item_id, org_id=org_id).first_or_404()
    return jsonify({"id": item.id, "name": item.name, "quantity": item.quantity})


@bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
@roles_required("pharmacist")
def update_item(item_id):
    org_id = get_jwt().get("org_id")
    item = Inventory.query.filter_by(id=item_id, org_id=org_id).first_or_404()
    payload = request.get_json() or {}
    item.name = payload.get("name", item.name)
    item.quantity = payload.get("quantity", item.quantity)
    db.session.commit()
    return jsonify({"id": item.id, "name": item.name, "quantity": item.quantity})


@bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
@roles_required("pharmacist")
def delete_item(item_id):
    org_id = get_jwt().get("org_id")
    item = Inventory.query.filter_by(id=item_id, org_id=org_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return "", 204
