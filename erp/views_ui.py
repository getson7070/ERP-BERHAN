from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user

from erp.models import UserDashboard, db

bp = Blueprint("ui", __name__)


@bp.route("/")
def root():
    return render_template("landing.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


@bp.route("/dashboard/customize", methods=["GET", "POST"])
@login_required
def customize_dashboard():
    record = UserDashboard.query.filter_by(user_id=current_user.id).first()

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        layout = payload.get("layout")
        if layout is None:
            layout = request.data.decode() or "{}"
        if not isinstance(layout, str):
            layout = str(layout)

        if record is None:
            record = UserDashboard(user_id=current_user.id, layout=layout)
            db.session.add(record)
        else:
            record.layout = layout
        db.session.commit()
        return jsonify(layout=record.layout), 200

    layout = record.layout if record and record.layout else "{}"
    return render_template("dashboard_customize.html", layout=layout)


__all__ = ["bp", "dashboard", "customize_dashboard", "root"]
