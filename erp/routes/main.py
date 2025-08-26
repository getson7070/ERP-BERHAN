from flask import Blueprint, render_template, session, redirect, url_for, request, current_app
from sqlalchemy import text
from erp.utils import login_required
from db import get_db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('auth.choose_login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'Client':
        return render_template('client_dashboard.html')
    if role == 'Employee':
        return render_template('employee_dashboard.html')
    conn = get_db(); cur = conn.cursor()
    cur.execute('SELECT name, query FROM saved_searches WHERE user_id = %s', (session.get("user_id"),))
    saved = cur.fetchall()
    cur.close(); conn.close()
    return render_template('analytics/dashboard.html', saved_searches=saved)

@bp.route('/dashboard/save_search', methods=['POST'])
@login_required
def save_search():
    name = request.form['name']
    query = request.form['query']
    conn = get_db(); cur = conn.cursor()
    cur.execute('INSERT INTO saved_searches (user_id, name, query) VALUES (%s,%s,%s)', (session.get('user_id'), name, query))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('main.dashboard'))


@bp.route('/search')
@login_required
def global_search():
    query = request.args.get('q', '')
    results = []
    if query:
        conn = get_db()
        pattern = f"%{query}%"
        sql = text(
            """
            SELECT 'CRM' AS module, name AS result FROM crm_customers
            WHERE org_id = :org AND LOWER(name) LIKE LOWER(:pattern)
            UNION ALL
            SELECT 'Inventory', name FROM inventory_items
            WHERE org_id = :org AND LOWER(name) LIKE LOWER(:pattern)
            UNION ALL
            SELECT 'HR', name FROM hr_employees
            WHERE org_id = :org AND LOWER(name) LIKE LOWER(:pattern)
            UNION ALL
            SELECT 'Finance', description FROM finance_transactions
            WHERE org_id = :org AND LOWER(description) LIKE LOWER(:pattern)
            """
        )
        cur = conn.execute(sql, {'org': session.get('org_id'), 'pattern': pattern})
        results = cur.fetchall()
        conn.close()
    return render_template('search_results.html', query=query, results=results)

@bp.route('/set_language/<lang>')
def set_language(lang):
    if lang in current_app.config['LANGUAGES']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.dashboard'))

@bp.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@bp.route('/plugins')
@login_required
def plugins_view():
    return render_template('plugins.html')
