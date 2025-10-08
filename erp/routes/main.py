from __future__ import annotations

import os
from flask import Blueprint, current_app, send_from_directory, url_for, redirect, request, make_response

# Register in app.py as: from .routes.main import bp as main_bp
bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    # Simple, self-contained landing to avoid template dependencies
    html = f"""
    <!doctype html>
    <html lang="en">
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>ERP Berhan</title>
      <style>
        body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu;background:#0f172a;color:#e5e7eb;display:grid;place-items:center;min-height:100dvh}}
        .card{{max-width:720px;padding:28px;border:1px solid #1f2937;border-radius:16px;background:linear-gradient(180deg,#0b1020,#0f172a)}}
        a{{color:#67e8f9;text-decoration:none}} a:hover{{text-decoration:underline}}
        .row{{margin-top:12px}}
      </style>
      <body>
        <main class="card">
          <h1>ERP Berhan</h1>
          <p>Service is up.</p>
          <div class="row"><a href="{url_for('main.choose_login')}">Sign in</a></div>
        </main>
      </body>
    </html>
    """
    return make_response(html, 200)

@bp.route("/choose-login")
def choose_login():
    # Minimal role picker that links to your /auth/login route (GET)
    base = "/auth/login"
    qs = lambda r: f"{base}?role={r}"
    html = f"""
    <!doctype html>
    <html lang="en">
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Choose role</title>
      <style>
        body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu;background:#0f172a;color:#e5e7eb;display:grid;place-items:center;min-height:100dvh}}
        .card{{max-width:680px;padding:28px;border:1px solid #1f2937;border-radius:16px;background:linear-gradient(180deg,#0b1020,#0f172a)}}
        a{{color:#67e8f9;text-decoration:none}} a:hover{{text-decoration:underline}}
        ul{{list-style:none;padding:0}} li{{margin:8px 0}}
      </style>
      <body>
        <main class="card">
          <h1>Choose a role</h1>
          <ul>
            <li><a href="{qs('admin')}">Admin</a></li>
            <li><a href="{qs('manager')}">Manager</a></li>
            <li><a href="{qs('employee')}">Employee</a></li>
          </ul>
          <p><a href="{url_for('main.index')}">← Back home</a></p>
        </main>
      </body>
    </html>
    """
    return make_response(html, 200)

@bp.route("/favicon.ico")
def favicon():
    """
    Prevent /favicon.ico from triggering a 404 (which then tries to render
    a missing errors/404.html). If the icon exists, serve it; otherwise 204.
    """
    try:
        static_folder = current_app.static_folder
        path = os.path.join(static_folder or "", "favicon.ico") if static_folder else None
        if path and os.path.exists(path):
            return send_from_directory(static_folder, "favicon.ico", mimetype="image/x-icon")
    except Exception:
        # Fall through to empty response on any error
        pass
    return ("", 204)

@bp.route("/healthz")
def healthz():
    return {"status": "ok"}, 200
