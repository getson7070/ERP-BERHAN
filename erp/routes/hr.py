# erp/routes/hr.py
from flask import Blueprint, jsonify
from erp.models import db, Employee

hr_bp = Blueprint("hr", __name__, url_prefix="/hr")

@hr_bp.route("/employees")
def list_employees():
    data = [
        {
            "id": e.id,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "email": e.email,
            "role": e.role,
            "is_active": e.is_active,
        }
        for e in Employee.query.order_by(Employee.id).limit(100).all()
    ]
    return jsonify(data)
