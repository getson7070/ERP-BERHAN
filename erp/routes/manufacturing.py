from flask import Blueprint, render_template, session, request, redirect, url_for
from db import get_db
from erp.workflow import require_enabled

bp = Blueprint("manufacturing", __name__, url_prefix="/manufacturing")


@bp.route("/")
@require_enabled("manufacturing")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name FROM manufacturing_jobs WHERE org_id = %s ORDER BY id",
        (session.get("org_id"),),
    )
    jobs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("manufacturing/index.html", jobs=jobs)


@bp.route("/add", methods=["GET", "POST"])
@require_enabled("manufacturing")
def add_job():
    if request.method == "POST":
        name = request.form["name"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO manufacturing_jobs (org_id, name) VALUES (%s,%s)",
            (session.get("org_id"), name),
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("manufacturing.index"))
    return render_template("manufacturing/add.html")
