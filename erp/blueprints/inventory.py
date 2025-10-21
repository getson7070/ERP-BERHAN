from flask import request, jsonify
from .models.inventory import db, Inventory

def create_item():
    data = request.get_json(force=True)
    item = Inventory(org_id=data.get("org_id", 1), name=data["name"], sku=data["sku"], quantity=data.get("quantity", 0))
    db.session.add(item); db.session.commit()
    return jsonify({"id": item.id}), 201

def list_items():
    items = Inventory.query.order_by(Inventory.id).all()
    return jsonify([{"id": i.id, "name": i.name, "sku": i.sku, "quantity": i.quantity} for i in items]), 200
