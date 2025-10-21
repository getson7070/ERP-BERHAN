from flask import Blueprint, jsonify
from ..celery_app import celery_app

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@bp.get("/vitals")
def vitals():
    return jsonify({"rps": 1.0, "error_rate": 0.0})

@celery_app.task()
def send_approval_reminders():
    return {"reminders_sent": 0, "status": "ok"}

@celery_app.task()
def forecast_sales(window: int = 7):
    return {"window": window, "forecast": [100] * window}
