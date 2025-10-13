from flask import Blueprint, render_template
from flask_login import login_required

crm_pipeline_bp = Blueprint("crm_pipeline", __name__, url_prefix="/crm", template_folder="../templates")

@crm_pipeline_bp.route("/pipeline")
@login_required
def pipeline():
    # Placeholder list; wire to your DB model later
    stages = [
        {"name": "New", "count": 0},
        {"name": "Qualified", "count": 0},
        {"name": "Proposal", "count": 0},
        {"name": "Won", "count": 0},
        {"name": "Lost", "count": 0},
    ]
    return render_template("crm/pipeline/index.html", stages=stages)
