from io import StringIO
import csv
_ITEMS: list[dict] = []

def create_item(sku: str, name: str, qty: int = 0):
    item = {'sku': sku, 'name': name, 'qty': int(qty)}
    _ITEMS.append(item); return item

def list_items():
    return list(_ITEMS)

def export_inventory_csv():
    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=['sku','name','qty'])
    w.writeheader(); w.writerows(_ITEMS)
    return buf.getvalue()
