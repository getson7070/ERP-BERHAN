# erp/auth/__init__.py

from __future__ import annotations

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
)
from werkzeug.security import check_password_hash

from erp.extensions import db, login_manager
from erp.models.user import User


bp = Blueprint("auth", __name__, url_prefix="/auth")


# -------- Flask-Login user loader --------
@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Tell Flask-Login how to reload a user from the session."""
    if not user_id:
        return None
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None

    # db.session.get() is the recommended SQLAlchemy 2.x pattern
    return db.session.get(User, uid)


# -------- Routes --------
@bp.route("/login", methods=["GET", "POST"])
def login():
    # If POST: validate credentials and log the user in
    if request.method == "POST":
        identifier = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        # Allow login via either email or username in the same field
        user = None
        if identifier:
            user = User.query.filter(
                (User.email == identifier) | (User.username == identifier)
            ).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash("Invalid email/username or password.", "danger")
            # 401 makes it obvious in logs without breaking UX
            return render_template("auth/login.html"), 401

        login_user(user)
        next_url = request.args.get("next") or url_for("main.dashboard")
        return redirect(next_url)

    # GET: just render the template (current_user will now work safely)
    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
