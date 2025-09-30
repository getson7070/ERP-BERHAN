# erp/routes/auth.py
from __future__ import annotations

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    make_response, jsonify
)
from werkzeug.security import check_password_hash
from sqlalchemy import text

# Import our DB shim and audit safely (no package-level cycles)
from db import get_db
from erp.audit import log_audit

# IMPORTANT:
# - Blueprint name must be "auth" so url_for("auth.login") resolves.
# - Export it as "auth_bp" so create_app() can register it.
auth_bp = Blueprint("auth", __name__, template_folder="../templates")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # GET: render HTML login page (preferred), with safe fallback if template missing.
    if request.method == "GET":
        try:
            # If your template lives at templates/auth/login.html this will work.
            # Adjust the path if your templates are organized differently.
            return render_template("auth/login.html")
        except Exception:
            # Safe fallback so deploy never 404s if template is missing
            html = """
            <!doctype html><meta charset="utf-8">
            <title>Login</title>
            <h1>Login</h1>
            <form method="post">
              <label>Email <input name="email" type="email" required></label><br>
              <label>Password <input name="password" type="password" required></label><br>
              <button type="submit">Sign in</button>
            </form>
            """
            return make_response(html, 200)

    # POST: minimal credential check (adjust to your schema/fields)
    email = (request.form.get("email") if request.form else None) or (
        request.json.get("email") if request.is_json else None
    )
    password = (request.form.get("password") if request.form else None) or (
        request.json.get("password") if request.is_json else None
    )

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    conn = get_db()
    try:
        # Adjust this query/columns to match your users table
        row = conn.execute(
            text("SELECT id, password_hash FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()
    finally:
        conn.close()

    if not row:
        log_audit(user_id=None, org_id=None, action="login_failed", details=f"email={email}")
        return jsonify({"error": "invalid credentials"}), 401

    user_id = row[0]
    password_hash = row[1]

    if not check_password_hash(password_hash, password):
        log_audit(user_id=None, org_id=None, action="login_failed", details=f"email={email}")
        return jsonify({"error": "invalid credentials"}), 401

    # Success: record audit and return OK. (If you have JWT/session, plug it here.)
    log_audit(user_id=user_id, org_id=None, action="login_success", details="")
    return jsonify({"ok": True, "user_id": int(user_id)}), 200


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    # Fill with your session/JWT invalidation as needed
    log_audit(user_id=None, org_id=None, action="logout", details="")
    # Send user back to login screen
    return redirect(url_for("auth.login"))


__all__ = ["auth_bp"]
