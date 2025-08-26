from flask import Blueprint, render_template, jsonify
from flask_login import login_required

hr_workflows_bp = Blueprint('hr_workflows', __name__, url_prefix='/hr')
# Alias for app factory imports
bp = hr_workflows_bp

@hr_workflows_bp.route('/recruitment')
@login_required
def recruitment():
    """Placeholder for recruitment workflow."""
    return render_template('hr/recruitment.html')

@hr_workflows_bp.route('/performance')
@login_required
def performance():
    """Placeholder for performance review workflow."""
    return render_template('hr/performance.html')
