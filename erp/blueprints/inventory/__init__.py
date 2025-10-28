from __future__ import annotations
from decimal import Decimal
from flask import Blueprint, session
from erp.models import db
from erp.models.inventory import Inventory

bp = Blueprint("inventory_bp", __name__, url_prefix="/inventory")

def get_jwt():
    # tests monkeypatch this to inject {"org_id": 1}
    return {"org_id": session.get("org_id")}

def _org_id_arg(org_id):
    return org_id if org_id is not None else (get_jwt() or {}).get("org_id")

def create_item(*, org_id: int | None = None, name: str, sku: str, quantity: int = 0, price: Decimal | int | float = 0):
    org_id = _org_id_arg(org_id)
    item = Inventory(org_id=org_id, name=name, sku=sku, quantity=int(quantity), price=price)
    db.session.add(item); db.session.commit()
    return item

def list_items(*, org_id: int | None = None):
    org_id = _org_id_arg(org_id)
    return Inventory.tenant_query(org_id).all()

def get_item(*, org_id: int | None = None, sku: str):
    org_id = _org_id_arg(org_id)
    return Inventory.tenant_query(org_id).filter_by(sku=sku).first()

def update_item(*, org_id: int | None = None, sku: str, **fields):
    item = get_item(org_id=org_id, sku=sku)
    if not item: return None
    for k, v in fields.items():
        if hasattr(item, k): setattr(item, k, v)
    db.session.commit()
    return item

__all__ = ["bp", "get_jwt", "create_item", "list_items", "get_item", "update_item"]




# --- AUTOAPPEND (safe) ---
def delete_item(*args, **kwargs):
    try:
        from .routes import delete_item as _real
        return _real(*args, **kwargs)
    except Exception as _e:
        raise NotImplementedError("delete_item not wired yet") from _e
