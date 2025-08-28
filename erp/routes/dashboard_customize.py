from flask import Blueprint, render_template, request, jsonify, session
from erp.utils import login_required
from erp.models import UserDashboard, db

bp = Blueprint("dashboard_custom", __name__, url_prefix="/dashboard")


@bp.route("/customize", methods=["GET", "POST"])
@login_required
def customize():
    """Render or persist the dashboard customization interface."""

    user_id = session.get("user_id")
    if request.method == "POST":
        payload = request.get_json() or {}
        layout = payload.get("layout", "{}")
        dash = UserDashboard.query.filter_by(user_id=user_id).first()
        if dash is None:
            dash = UserDashboard(user_id=user_id, layout=layout)
            db.session.add(dash)
        else:
            dash.layout = layout
        db.session.commit()
        return jsonify({"status": "ok"})

    dash = UserDashboard.query.filter_by(user_id=user_id).first()
    layout = dash.layout if dash else "{}"
    return render_template("customize_dashboard.html", layout=layout)
