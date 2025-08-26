from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db
from erp.cache import cache_get, cache_set, cache_invalidate

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/')
def index():
    org_id = session.get("org_id")
    cache_key = f"inventory:{org_id}"
    items = cache_get(cache_key)
    if items is None:
        conn = get_db(); cur = conn.cursor()
        cur.execute('SELECT id, name, quantity FROM inventory_items WHERE org_id = %s ORDER BY id', (org_id,))
        items = cur.fetchall()
        cache_set(cache_key, items)
        cur.close(); conn.close()
    return render_template('inventory/index.html', items=items)

@bp.route('/add', methods=['GET','POST'], endpoint='add_inventory')
def add_inventory():
    if request.method == 'POST':
        name = request.form['name']; qty = request.form['quantity']
        conn = get_db(); cur = conn.cursor()
        org_id = session.get('org_id')
        cur.execute('INSERT INTO inventory_items (org_id, name, quantity) VALUES (%s,%s,%s)', (org_id, name, qty))
        conn.commit(); cur.close(); conn.close()
        cache_invalidate(f"inventory:{org_id}")
        return redirect(url_for('inventory.index'))
    return render_template('inventory/add.html')
