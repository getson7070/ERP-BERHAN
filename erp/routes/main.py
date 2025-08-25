from flask import Blueprint, redirect, url_for
from erp.utils import login_required

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return redirect(url_for('auth.choose_login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('analytics.dashboard'))
