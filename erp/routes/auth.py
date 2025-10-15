from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from ..extensions import login_manager, db
from ..models import User
from ..forms import LoginForm

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")

@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("inventory.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            flash("Welcome back!", "success")
            next_url = request.args.get("next") or url_for("inventory.index")
            return redirect(next_url)
        flash("Invalid credentials.", "danger")
    return render_template("auth/login.html", form=form)

@auth_bp.get("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("auth.login"))
