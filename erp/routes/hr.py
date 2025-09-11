from flask import Blueprint, render_template, session, request, redirect, url_for

from erp.extensions import db
from erp.models import Employee
from erp.utils import login_required
from erp.workflow import require_enabled

bp = Blueprint("hr", __name__, url_prefix="/hr")


@bp.route("/")
@login_required
@require_enabled("hr")
def index():
    employees = Employee.tenant_query().order_by(Employee.id).all()
    return render_template("hr/index.html", employees=employees)


@bp.route("/add", methods=["GET", "POST"])
@login_required
@require_enabled("hr")
def add_employee():
    if request.method == "POST":
        name = request.form["name"]
        emp = Employee(org_id=session.get("org_id"), name=name)
        db.session.add(emp)
        db.session.commit()
        return redirect(url_for("hr.index"))
    return render_template("hr/add.html")
