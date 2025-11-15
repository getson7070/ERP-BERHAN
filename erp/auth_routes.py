from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func

from .extensions import db
from .models import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Simple email/password login.

    - If the user is already authenticated, send them to the dashboard.
    - On POST, validate credentials and log them in.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if not email or not password:
            error = "Email and password are required."
        else:
            # Case-insensitive lookup by email
            user = (
                User.query.filter(func.lower(User.email) == email.lower())
                .first()
            )

            if user is None or not user.check_password(password):
                error = "Invalid email or password."
            else:
                login_user(user)
                next_url = request.args.get("next") or url_for("dashboard")
                return redirect(next_url)

    # Even when there is an error, we render the same template
    return render_template("auth/login.html", error=error)


@bp.route("/logout")
@login_required
def logout():
    """Terminate the session and send the user back to the login page."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
