from flask import Blueprint, redirect, render_template, url_for, session, request, current_app
from erp.utils import login_required

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
    return render_template('analytics/dashboard.html')


@bp.route('/set_language/<lang>')
def set_language(lang):
    if lang in current_app.config['LANGUAGES']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.dashboard'))


@bp.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')
