from flask import Blueprint, render_template, jsonify
from flask_login import login_required

bp = Blueprint('hr_workflows', __name__, url_prefix='/hr')

@bp.route('/recruitment')
@login_required
def recruitment():
    """Placeholder for recruitment workflow."""
    return render_template('hr/recruitment.html')

@bp.route('/performance')
@login_required
def performance():
    """Placeholder for performance review workflow."""
    return render_template('hr/performance.html')
