from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__)

@api_bp.get("/ping")
def ping():
    return jsonify({"pong": True})
