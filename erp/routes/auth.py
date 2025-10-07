from flask import Blueprint, render_template, request, redirect, url_for

# name="auth" so endpoints look like "auth.login"
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    role = (request.args.get("role") or "client").lower()
    if request.method == "POST":
        # TODO: insert real authentication here
        return redirect(url_for("index"))
    return render_template("auth/login.html", role=role)


# Back-compat: keep the old direct role URLs working
@auth_bp.route("/auth/employee_login", methods=["GET", "POST"])
def employee_login():
    return login()


@auth_bp.route("/auth/client_login", methods=["GET", "POST"])
def client_login():
    return login()
