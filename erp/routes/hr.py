from flask import Blueprint, render_template, session, request, redirect, url_for
from db import get_db
from erp.workflow import require_enabled

bp = Blueprint('hr', __name__, url_prefix='/hr')

@bp.route('/')
@require_enabled('hr')
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM hr_employees WHERE org_id = %s ORDER BY id', (session.get('org_id'),))
    employees = cur.fetchall()
    cur.close(); conn.close()
    return render_template('hr/index.html', employees=employees)


@bp.route('/add', methods=['GET', 'POST'])
@require_enabled('hr')
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db(); cur = conn.cursor()
        cur.execute('INSERT INTO hr_employees (org_id, name) VALUES (%s,%s)', (session.get('org_id'), name))
        conn.commit(); cur.close(); conn.close()
        return redirect(url_for('hr.index'))
    return render_template('hr/add.html')
