from flask import Blueprint, jsonify

bp = Blueprint("finance_approval", __name__)


@bp.post("/approvals/submit")
def submit():
    return jsonify({"ok": True})
