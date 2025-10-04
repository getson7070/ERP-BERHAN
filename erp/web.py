# erp/web.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from jinja2 import TemplateNotFound, TemplateSyntaxError

web_bp = Blueprint("web", __name__)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
ENTRY_TEMPLATE = os.getenv("ENTRY_TEMPLATE", "").strip()  # e.g. "auth/login.html"

def _try_render(candidates):
    for name in candidates:
        try:
            return render_template(name)
        except TemplateNotFound as e:
            current_app.logger.error(f"[templates] TemplateNotFound while rendering '{name}': missing '{e.name}'")
        except TemplateSyntaxError as e:
            current_app.logger.error(f"[templates] Syntax error in '{name}' at line {e.lineno}: {e.message}")
        except Exception as e:
            current_app.logger.exception(f"[templates] Unexpected error rendering '{name}': {e}")
    return None

@web_bp.route("/")
def home():
    # allow override via env for deterministic testing
    if ENTRY_TEMPLATE:
        page = _try_render([ENTRY_TEMPLATE])
        if page:
            return page
        current_app.logger.warning(f"[entry] ENTRY_TEMPLATE='{ENTRY_TEMPLATE}' could not be rendered; falling back.")

    page = _try_render([
        "auth/login.html",
        "choose_login.html",
        "login.html",
        "index.html",
    ])
    if page:
        return page

    current_app.logger.warning("No entry template found under templates/ or erp/templates/.")
    return (
        "<h2>ERP-BERHAN is running.</h2>"
        "Expected one of: <code>templates/auth/login.html</code>, "
        "<code>templates/choose_login.html</code>, <code>templates/login.html</code>, "
        "<code>templates/index.html</code>.<br><br>"
        "Health: <a href='/health'>/health</a>",
        200,
    )

@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["user"] = u
            return redirect(url_for("web.dashboard"))
        flash("Invalid credentials", "error")
    page = _try_render(["auth/login.html", "login.html", "choose_login.html"])
    return page or ("<h3>Missing login templates.</h3>", 200)

@web_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("web.login"))
    page = _try_render(["dashboard.html", "analytics/dashboard.html", "index.html"])
    return page or ("<h3>Missing dashboard template.</h3>", 200)

# Temporary, safe diagnostics: shows active loader search paths
@web_bp.route("/__templates")
def __templates():
    env = current_app.jinja_env
    loaders = getattr(env.loader, "loaders", [env.loader])
    lines = [f"<h3>Jinja search paths</h3><ul>"]
    for l in loaders:
        if hasattr(l, "searchpath"):
            for p in getattr(l, "searchpath", []):
                lines.append(f"<li>{p}</li>")
    lines.append("</ul>")
    return "\n".join(lines), 200
