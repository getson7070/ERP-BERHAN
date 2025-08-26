from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db
from erp.workflow import require_enabled

bp = Blueprint('finance', __name__, url_prefix='/finance')

@bp.route('/')
@require_enabled('finance')
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, amount, description, status FROM finance_transactions WHERE org_id = %s ORDER BY id', (session.get("org_id"),))
    transactions = cur.fetchall()
    cur.close(); conn.close()
    return render_template('finance/index.html', transactions=transactions)

@bp.route('/add', methods=['GET', 'POST'])
@require_enabled('finance')
def add_transaction():
    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        conn = get_db(); cur = conn.cursor()
        cur.execute('INSERT INTO finance_transactions (org_id, amount, description, status) VALUES (%s,%s,%s,%s)', (session.get('org_id'), amount, description, 'pending'))
        conn.commit(); cur.close(); conn.close()
        return redirect(url_for('finance.index'))
    return render_template('finance/add.html')
