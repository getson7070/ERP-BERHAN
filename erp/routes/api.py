# erp/routes/api.py
from flask import Blueprint, jsonify
from flask_limiter.util import get_remote_address
from erp.extensions import limiter

api_bp = Blueprint("api", __name__)

@api_bp.get("/ping")
@limiter.limit("10 per second")
def ping():
    return jsonify(ok=True)
