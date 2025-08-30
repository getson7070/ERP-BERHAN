from flask import Blueprint, render_template, session, request, redirect, url_for
from db import get_db
from erp.workflow import require_enabled
from erp.cache import cache_get, cache_set, cache_invalidate

bp = Blueprint("crm", __name__, url_prefix="/crm")


@bp.route("/")
@require_enabled("crm")
def index():
    org_id = session.get("org_id")
    cache_key = f"crm:{org_id}"
    customers = cache_get(cache_key)
    if customers is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name FROM crm_customers WHERE org_id = %s ORDER BY id",
            (org_id,),
        )
        customers = cur.fetchall()
        cache_set(cache_key, customers)
        cur.close()
        conn.close()
    return render_template("crm/index.html", customers=customers)


@bp.route("/add", methods=["GET", "POST"])
@require_enabled("crm")
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        conn = get_db()
        cur = conn.cursor()
        org_id = session.get("org_id")
        cur.execute(
            "INSERT INTO crm_customers (org_id, name) VALUES (%s,%s)", (org_id, name)
        )
        conn.commit()
        cur.close()
        conn.close()
        cache_invalidate(f"crm:{org_id}")
        return redirect(url_for("crm.index"))
    return render_template("crm/add.html")
