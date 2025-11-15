"""Self-service report builder endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user

bp = Blueprint("report_builder", __name__, url_prefix="/reports")


@bp.get("/builder")
@login_required
def builder_view():
    return render_template("report_builder.html", user=current_user)


@bp.post("/run")
@login_required
def run_report():
    payload = request.get_json(silent=True) or {}
    config = payload.get("config", {})
    return jsonify(data=[], meta={"config": config})


__all__ = ["bp", "builder_view", "run_report"]
