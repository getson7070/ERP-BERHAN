# erp/routes/auth.py
from flask import Blueprint, redirect, url_for
from erp.extensions import limiter, oauth

bp = Blueprint("auth", __name__)

@bp.route("/login")
@limiter.limit("20/minute")
def login():
    # your oauth flow...
    return redirect(url_for("home"))
