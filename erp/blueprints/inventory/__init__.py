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
