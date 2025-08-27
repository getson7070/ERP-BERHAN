"""User feedback collection endpoints."""
from flask import Blueprint, current_app, request, render_template

bp = Blueprint('feedback', __name__, url_prefix='/feedback')


@bp.get('/')
def form():
    return render_template('feedback.html')


@bp.post('/')
def submit():
    data = request.get_json() or {}
    current_app.logger.info("user_feedback", extra={'feedback': data})
    return ('', 204)
