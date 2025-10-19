# erp/routes/dashboard_customize.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from erp.extensions import db
from erp.models import UserDashboard

dashboard_customize_bp = Blueprint("dashboard_customize", __name__, url_prefix="/api/dashboard")

@login_required
@dashboard_customize_bp.get("/layout")
def get_layout():
    row = UserDashboard.query.filter_by(user_id=current_user.id).first()
    return jsonify(row.layout if row and row.layout else {}), 200

@login_required
@dashboard_customize_bp.post("/layout")
def save_layout():
    payload = request.get_json(silent=True) or {}
    row = UserDashboard.query.filter_by(user_id=current_user.id).first()
    if not row:
        row = UserDashboard(user_id=current_user.id, layout=payload)
        db.session.add(row)
    else:
        row.layout = payload
    db.session.commit()
    return jsonify({"ok": True}), 200


