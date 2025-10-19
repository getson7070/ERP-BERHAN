from __future__ import annotations
from flask import Blueprint, render_template_string
from erp.utils import login_required
from erp.db import db, PrivacyImpactAssessment

bp = Blueprint("privacy", __name__)

@bp.route("/privacy")
@login_required
def index():
    items = (
        PrivacyImpactAssessment.query
        .order_by(PrivacyImpactAssessment.assessment_date.desc())
        .all()
    )
    # Simple HTML that includes expected fields
    html = """
    <h1>Privacy Dashboard</h1>
    <ul>
    {% for it in items %}
      <li class="pia">
        <span class="feature">{{ it.feature_name }}</span>
        <span class="status">{{ it.status }}</span>
        <span class="risk">{{ it.risk_rating }}</span>
      </li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html, items=items)
