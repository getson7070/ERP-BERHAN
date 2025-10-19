from typing import Any, List

def _Inventory():
    # lazy import to avoid import cycles during tests
    from erp.models import Inventory as _Inv  # type: ignore
    return _Inv

def get_item(session, item_id: Any):
    Inv = _Inventory()
    try:
        return session.get(Inv, item_id)
    except AttributeError:
        # SQLAlchemy <2 compat
        return session.query(Inv).get(item_id)

def create_item(session, **fields):
    Inv = _Inventory()
    obj = Inv(**fields)
    session.add(obj)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return obj

def list_items(session) -> List[Any]:
    Inv = _Inventory()
    return list(session.query(Inv).all())

def export_items(session) -> List[dict]:
    rows = list_items(session)
    out = []
    for r in rows:
        if hasattr(r, "to_dict"):
            out.append(r.to_dict())
        else:
            d = {}
            for k in ("id", "name", "sku", "quantity"):
                if hasattr(r, k):
                    d[k] = getattr(r, k)
            out.append(d)
    return out

# ---- inventory public API shims (service-backed with in-memory fallback) ----
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List

# Try to use a real service implementation if present
try:
    from .service import (  # type: ignore
        create_item as _svc_create_item,
        get_item as _svc_get_item,
        update_item as _svc_update_item,
        delete_item as _svc_delete_item,
        list_items as _svc_list_items,
    )
except Exception:
    _svc_create_item = _svc_get_item = _svc_update_item = _svc_delete_item = _svc_list_items = None

# Minimal in-memory fallback (ids auto-increment)
_INV_STORE: Dict[int, Dict[str, Any]] = {}
_INV_NEXT_ID = 1

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _fb_create_item(data: Dict[str, Any]) -> Dict[str, Any]:
    global _INV_NEXT_ID
    item = dict(data)
    item.setdefault("name", f"item-{_INV_NEXT_ID}")
    item.setdefault("quantity", 0)
    item.setdefault("price", 0.0)
    item["id"] = _INV_NEXT_ID
    item["created_at"] = _now_iso()
    item["updated_at"] = item["created_at"]
    _INV_STORE[_INV_NEXT_ID] = item
    _INV_NEXT_ID += 1
    return item

def _fb_get_item(item_id: int) -> Dict[str, Any] | None:
    return _INV_STORE.get(int(item_id))

def _fb_update_item(item_id: int, **fields: Any) -> Dict[str, Any]:
    item = _INV_STORE.get(int(item_id))
    if item is None:
        raise KeyError(f"item {item_id} not found")
    item.update(fields)
    item["updated_at"] = _now_iso()
    return item

def _fb_delete_item(item_id: int) -> bool:
    return _INV_STORE.pop(int(item_id), None) is not None

def _fb_list_items() -> List[Dict[str, Any]]:
    return list(_INV_STORE.values())

# Public functions (exported symbols)
def create_item(data: Dict[str, Any]) -> Dict[str, Any]:
    if _svc_create_item:  # real service
        return _svc_create_item(data)
    return _fb_create_item(data)

def get_item(item_id: int) -> Dict[str, Any] | None:
    if _svc_get_item:
        return _svc_get_item(item_id)
    return _fb_get_item(item_id)

def update_item(item_id: int, **fields: Any) -> Dict[str, Any]:
    if _svc_update_item:
        return _svc_update_item(item_id, **fields)
    return _fb_update_item(item_id, **fields)

def delete_item(item_id: int) -> bool:
    if _svc_delete_item:
        return _svc_delete_item(item_id)
    return _fb_delete_item(item_id)

def list_items() -> List[Dict[str, Any]]:
    if _svc_list_items:
        return _svc_list_items()
    return _fb_list_items()

__all__ = ["create_item", "get_item", "update_item", "delete_item", "list_items"]
# ---- /inventory public API shims ----
