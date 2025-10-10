# erp/routes/main.py
from flask import Blueprint, render_template, redirect, url_for, request

bp = Blueprint("main", __name__)

@bp.get("/")
def root():
    return redirect(url_for("main.choose_login"))

@bp.get("/choose_login")
def choose_login():
    # Only client login link is active. Others are visually present but disabled/hidden.
    return render_template("choose_login.html")
