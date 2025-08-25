from flask import Blueprint, redirect, render_template, url_for
from erp.utils import login_required

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return redirect(url_for('auth.choose_login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('analytics.dashboard'))


@bp.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')
