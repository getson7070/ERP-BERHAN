from flask import Blueprint, render_template, request

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "client")
    if request.method == "GET":
        return render_template("auth/login.html", role=role)
    # TODO: add your real auth here
    return render_template("auth/login.html", role=role, error="Not implemented yet")
