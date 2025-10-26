from flask import Blueprint

recall_bp = Blueprint('recall', __name__)

@recall_bp.route('/recall')
def recall():
    return "Recall function"

integration_bp = Blueprint('integration', __name__)

@integration_bp.route('/integrate')
def integrate():
    return "Integration"
