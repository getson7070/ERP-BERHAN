from flask import Blueprint, render_template, session, request, redirect, url_for
from sqlalchemy import text
from db import get_db
from erp.workflow import require_enabled

bp = Blueprint("procurement", __name__, url_prefix="/procurement")


@bp.route("/")
@require_enabled("procurement")
def index():
    conn = get_db()
    suppliers = conn.execute(
        text(
            "SELECT id, name FROM procurement_suppliers WHERE org_id = :org ORDER BY id"
        ),
        {"org": session.get("org_id")},
    ).fetchall()
    conn.close()
    return render_template("procurement/index.html", suppliers=suppliers)


@bp.route("/add", methods=["GET", "POST"])
@require_enabled("procurement")
def add_supplier():
    if request.method == "POST":
        name = request.form["name"]
        conn = get_db()
        conn.execute(
            text(
                "INSERT INTO procurement_suppliers (org_id, name) VALUES (:org, :name)"
            ),
            {"org": session.get("org_id"), "name": name},
        )
        conn.commit()
        conn.close()
        return redirect(url_for("procurement.index"))
    return render_template("procurement/add.html")
