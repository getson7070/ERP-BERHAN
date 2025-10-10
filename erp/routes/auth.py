# erp/routes/auth.py
from flask import Blueprint, request, render_template, abort

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET"])
def login():
    role = request.args.get("role", "client")
    # Only 'client' is publicly reachable from choose_login; other roles will have hidden links unless authenticated.
    if role not in {"client", "employee", "admin"}:
        abort(400)
    return render_template("auth/login.html", role=role)
