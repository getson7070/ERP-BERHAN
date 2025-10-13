
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from erp.extensions import db
from .models import Lead, Opportunity

crm_bp = Blueprint("crm", __name__, url_prefix="/crm")

@crm_bp.route("/leads", methods=["GET","POST"])
@login_required
def leads():
    if request.method == "POST":
        data = request.get_json() or {}
        obj = Lead(name=data["name"])
        db.session.add(obj); db.session.commit()
        return jsonify({"id": str(obj.id)}), 201
    rows = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template("crm/leads.html", leads=rows)

@crm_bp.route("/opportunities", methods=["GET","POST"])
@login_required
def opportunities():
    if request.method == "POST":
        data = request.get_json() or {}
        obj = Opportunity(title=data["title"], value=data.get("value",0))
        db.session.add(obj); db.session.commit()
        return jsonify({"id": str(obj.id)}), 201
    rows = Opportunity.query.order_by(Opportunity.title).all()
    return render_template("crm/opportunities.html", opportunities=rows)
