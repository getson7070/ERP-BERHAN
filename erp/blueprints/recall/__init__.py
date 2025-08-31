"""Endpoints for recall simulations."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_security import auth_required, roles_required

from ...inventory import Lot, Serial

bp = Blueprint("recall", __name__, url_prefix="/api")


@bp.post("/recall-simulate")
@auth_required("token")
@roles_required("auditor")
def recall_simulate():
    """Generate a recall report for a given lot number."""
    data = request.get_json() or {}
    lot_number = data.get("lot_number", "")
    lot = Lot.query.filter_by(lot_number=lot_number).first_or_404()
    serials = [s.serial_number for s in Serial.query.filter_by(lot_id=lot.id)]
    return jsonify({"lot_number": lot.lot_number, "serials": serials})
