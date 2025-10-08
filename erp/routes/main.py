from flask import Blueprint, render_template, current_app, send_from_directory
from jinja2 import TemplateNotFound
import os, secrets

main = Blueprint("main", __name__)

# Safety net: ensure a SECRET_KEY exists so sessions/flash/login don't crash in dev
@main.before_app_request
def _ensure_secret_key():
    app = current_app
    if not app.config.get("SECRET_KEY"):
        # Prefer environment variable if present
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or ("dev-" + secrets.token_hex(32))

@main.route("/")
def index():
    try:
        return render_template("index.html")
    except TemplateNotFound:
        # Minimal fallback page
        return (
            "<h1>ERP Backend</h1>"
            '<p><a href="/choose-login">Choose role to log in</a></p>',
            200,
        )

@main.route("/choose-login")
def choose_login():
    # Try to render template; otherwise return a tiny inline page
    try:
        return render_template("choose_login.html")
    except TemplateNotFound:
        roles = ["admin", "manager", "employee"]
        links = "".join(f'<li><a href="/auth/login?role={r}">{r.title()} Login</a></li>' for r in roles)
        return f"<h2>Choose Login</h2><ul>{links}</ul>", 200

@main.route("/favicon.ico")
def favicon():
    # Serve favicon if it exists; otherwise return 204 to avoid 404 noise
    static_dir = os.path.join(current_app.root_path, "static")
    ico_path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(ico_path):
        return send_from_directory(static_dir, "favicon.ico")
    return ("", 204)

@main.route("/healthz")
def healthz():
    return {"ok": True}, 200
