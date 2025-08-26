from flask import Blueprint, render_template
from flask_login import login_required

# Blueprint for dashboard customization
# Allows users to access a page where they can customize their dashboard layout.
dashboard_custom_bp = Blueprint('dashboard_custom', __name__, url_prefix='/dashboard')
# Alias for app factory imports
bp = dashboard_custom_bp

@dashboard_custom_bp.route('/customize', methods=['GET'])
@login_required
def customize():
    """Render the dashboard customization interface.

    This view renders a template with placeholder content for a drag-and-drop
    dashboard builder. In a full implementation, this would load the user's
    existing widget layout and provide controls for adding, removing and
    arranging dashboard widgets.
    """
    return render_template('customize_dashboard.html')
