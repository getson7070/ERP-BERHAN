from flask import Blueprint, render_template, session, request, redirect, url_for
from db import get_db
from erp.workflow import require_enabled

bp = Blueprint("projects", __name__, url_prefix="/projects")


@bp.route("/")
@require_enabled("projects")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name FROM project_projects WHERE org_id = %s ORDER BY id",
        (session.get("org_id"),),
    )
    projects = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("projects/index.html", projects=projects)


@bp.route("/add", methods=["GET", "POST"])
@require_enabled("projects")
def add_project():
    if request.method == "POST":
        name = request.form["name"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO project_projects (org_id, name) VALUES (%s,%s)",
            (session.get("org_id"), name),
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("projects.index"))
    return render_template("projects/add.html")
