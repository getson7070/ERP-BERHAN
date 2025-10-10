# erp/routes/auth.py
from flask import Blueprint, render_template, request, abort

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["GET"])
def login():
    # role is a query param (?role=client|employee|admin)
    role = request.args.get("role", "client").lower()
    if role not in {"client", "employee", "admin"}:
        abort(404)

    # guard: only client is public; other roles return 404 from public page
    if role != "client":
        # later you can replace this with `@login_required` or SSO checks
        abort(404)

    return render_template("auth/login.html", role=role)
