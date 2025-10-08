from flask import Blueprint, render_template, current_app, send_from_directory
from jinja2 import TemplateNotFound
import os, secrets

# IMPORTANT: export as `bp` (your app imports this name)
bp = Blueprint("main", __name__)

# Safety net: ensure a SECRET_KEY so sessions/flash don't crash in dev
@bp.before_app_request
def _ensure_secret_key():
    app = current_app
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or ("dev-" + secrets.token_hex(32))

@bp.route("/")
def index():
    try:
        return render_template("index.html")
    except TemplateNotFound:
        return (
            "<h1>ERP Backend</h1>"
            '<p><a href="/choose-login">Choose role to log in</a></p>',
            200,
        )

@bp.route("/choose-login")
def choose_login():
    try:
        return render_template("choose_login.html")
    except TemplateNotFound:
        roles = ["admin", "manager", "employee"]
        links = "".join(f'<li><a href="/auth/login?role={r}">{r.title()} Login</a></li>' for r in roles)
        return f"<h2>Choose Login</h2><ul>{links}</ul>", 200

@bp.route("/favicon.ico")
def favicon():
    static_dir = os.path.join(current_app.root_path, "static")
    ico_path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(ico_path):
        return send_from_directory(static_dir, "favicon.ico")
    return ("", 204)

@bp.route("/healthz")
def healthz():
    return {"ok": True}, 200
