# erp/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("auth", __name__)

@bp.route("/auth/login", methods=["GET", "POST"])
def login():
    role = (request.args.get("role") or "client").lower()

    # TODO: add real authentication here (lookup user, verify password / 2FA, etc.)
    if request.method == "POST":
        # For now just bounce home; wire up your auth logic later.
        return redirect(url_for("index"))

    # This is the styled login page you already have:
    return render_template("auth/login.html", role=role)

# Back-compat routes if something references them
@bp.route("/auth/employee_login", methods=["GET", "POST"])
def employee_login():
    return login()

@bp.route("/auth/client_login", methods=["GET", 'POST'])
def client_login():
    return login()
