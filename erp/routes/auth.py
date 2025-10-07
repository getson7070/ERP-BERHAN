# erp/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for

auth_bp = Blueprint("auth", __name__)  # <-- exported name that app.py imports

@auth_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    role = (request.args.get("role") or "client").lower()
    if request.method == "POST":
        # TODO: real login logic
        return redirect(url_for("index"))
    return render_template("auth/login.html", role=role)

# Back-compat routes (they just call the same view)
@auth_bp.route("/auth/employee_login", methods=["GET", "POST"])
def employee_login():
    return login()

@auth_bp.route("/auth/client_login", methods=["GET", "POST"])
def client_login():
    return login()
