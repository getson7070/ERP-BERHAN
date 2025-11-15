from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Iterable

from flask import Blueprint, jsonify, request, session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, NotFound

from erp.models import db
from erp.models.inventory import Inventory

bp = Blueprint("inventory_bp", __name__, url_prefix="/inventory")


@dataclass(slots=True)
class InventoryDTO:
    id: int
    org_id: int
    name: str
    sku: str
    quantity: int
    price: Decimal


def get_jwt() -> dict[str, Any] | None:
    """Fetch the session-stored identity payload, if present."""

    token = session.get("jwt")
    if isinstance(token, dict):
        return token
    return None


def _resolve_org_id(explicit: int | None) -> int:
    org_id = explicit
    if org_id is None:
        payload = get_jwt() or {}
        org_id = payload.get("org_id")
    if org_id is None:
        raise BadRequest("Organisation context is required")
    return int(org_id)


def _serialise(item: Inventory) -> InventoryDTO:
    return InventoryDTO(
        id=item.id,
        org_id=item.org_id,
        name=item.name,
        sku=item.sku,
        quantity=item.quantity,
        price=item.price,
    )


def _apply_updates(item: Inventory, fields: dict[str, Any]) -> None:
    mutable = {"name", "sku", "quantity", "price"}
    for key, value in fields.items():
        if key not in mutable:
            continue
        if key == "quantity":
            value = int(value)
        if key == "price":
            value = Decimal(str(value))
        setattr(item, key, value)


def _paginate(query, *, limit: int | None, offset: int | None) -> Iterable[Inventory]:
    if limit is not None:
        query = query.limit(min(limit, 100))
    if offset:
        query = query.offset(max(offset, 0))
    return db.session.execute(query).scalars().all()


@bp.post("/")
def create_item() -> tuple[Any, int]:
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    sku = payload.get("sku")
    if not name or not sku:
        raise BadRequest("Both name and sku are required")

    org_id = _resolve_org_id(payload.get("org_id"))
    quantity = int(payload.get("quantity", 0))
    price = Decimal(str(payload.get("price", 0)))

    item = Inventory(org_id=org_id, name=name.strip(), sku=sku.strip(), quantity=quantity, price=price)
    db.session.add(item)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise

    return jsonify(asdict(_serialise(item))), 201


@bp.get("/")
def list_items():
    org_id = _resolve_org_id(request.args.get("org_id", type=int))
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", type=int)

    stmt = select(Inventory).where(Inventory.org_id == org_id).order_by(Inventory.id.asc())
    items = _paginate(stmt, limit=limit, offset=offset)
    return jsonify([asdict(_serialise(item)) for item in items])


@bp.get("/<int:item_id>")
def get_item(item_id: int):
    org_id = _resolve_org_id(request.args.get("org_id", type=int))
    item = db.session.get(Inventory, item_id)
    if not item or item.org_id != org_id:
        raise NotFound("Inventory item not found")
    return jsonify(asdict(_serialise(item)))


@bp.patch("/<int:item_id>")
@bp.put("/<int:item_id>")
def update_item(item_id: int):
    payload = request.get_json(silent=True) or {}
    if not payload:
        raise BadRequest("Update payload required")

    org_id = _resolve_org_id(payload.get("org_id") or request.args.get("org_id", type=int))
    item = db.session.get(Inventory, item_id)
    if not item or item.org_id != org_id:
        raise NotFound("Inventory item not found")

    _apply_updates(item, payload)
    db.session.commit()
    return jsonify(asdict(_serialise(item)))


@bp.delete("/<int:item_id>")
def delete_item(item_id: int):
    org_id = _resolve_org_id(request.args.get("org_id", type=int))
    item = db.session.get(Inventory, item_id)
    if not item or item.org_id != org_id:
        raise NotFound("Inventory item not found")

    db.session.delete(item)
    db.session.commit()
    return "", 204


__all__ = [
    "bp",
    "get_jwt",
    "create_item",
    "list_items",
    "get_item",
    "update_item",
    "delete_item",
]
