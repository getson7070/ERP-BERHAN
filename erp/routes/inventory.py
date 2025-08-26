from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, jsonify
from sqlalchemy import text
from db import get_db
from erp.cache import cache_get, cache_set, cache_invalidate

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/')
def index():
    org_id = session.get("org_id")
    cache_key = f"inventory:{org_id}"
    items = cache_get(cache_key)
    if items is None:
        conn = get_db()
        query = text('SELECT id, name, quantity FROM inventory_items WHERE org_id = :org ORDER BY id')
        cur = conn.execute(query, {'org': org_id})
        items = cur.fetchall()
        cache_set(cache_key, items)
        cur.close()
        conn.close()
    if current_app.config.get('TESTING'):
        return jsonify([{'id': i[0], 'name': i[1], 'quantity': i[2]} for i in items])
    return render_template('inventory/index.html', items=items)

@bp.route('/add', methods=['GET','POST'], endpoint='add_inventory')
def add_inventory():
    if request.method == 'POST':
        name = request.form['name']; qty = request.form['quantity']
        conn = get_db()
        org_id = session.get('org_id')
        insert = text('INSERT INTO inventory_items (org_id, name, quantity) VALUES (:org, :name, :qty)')
        conn.execute(insert, {'org': org_id, 'name': name, 'qty': qty})
        conn.commit()
        conn.close()
        cache_invalidate(f"inventory:{org_id}")
        return redirect(url_for('inventory.index'))
    return render_template('inventory/add.html')
