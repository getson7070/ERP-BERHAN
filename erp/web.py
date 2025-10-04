# erp/web.py
import os
from flask import (
    Blueprint, render_template, request, redirect, url_for, session,
    current_app, flash
)
from jinja2 import TemplateNotFound, TemplateSyntaxError

# Try to use your real LoginForm if present; otherwise provide a safe fallback.
try:
    # adapt these import paths if you already have a form class elsewhere
    from erp.forms.auth import LoginForm as _RealLoginForm  # noqa: F401
    LoginForm = _RealLoginForm
except Exception:
    # Fallback: minimal Flask-WTF form
    try:
        from flask_wtf import FlaskForm
        from wtforms import StringField, PasswordField
        from wtforms.validators import DataRequired
        class LoginForm(FlaskForm):
            class Meta:  # CSRF can stay on if SECRET_KEY is set; off also works
                csrf = False
            username = StringField("Username", validators=[DataRequired()])
            password = PasswordField("Password", validators=[DataRequired()])
    except Exception:
        LoginForm = None  # absolute last resort; we’ll still render without fields

web_bp = Blueprint("web", __name__)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
ENTRY_TEMPLATE = os.getenv("ENTRY_TEMPLATE", "").strip()  # e.g., "auth/login.html"


def _try_render(template_name, **ctx):
    try:
        return render_template(template_name, **ctx)
    except TemplateNotFound as e:
        current_app.logger.error(
            f"[templates] TemplateNotFound while rendering '{template_name}': missing '{e.name}'"
        )
    except TemplateSyntaxError as e:
        current_app.logger.error(
            f"[templates] Syntax error in '{template_name}' at line {e.lineno}: {e.message}"
        )
    except Exception as e:
        current_app.logger.exception(f"[templates] Unexpected error rendering '{template_name}': {e}")
    return None


@web_bp.route("/")
def home():
    # Root should show login so the required context ('form') is available.
    # If you *really* want to force a different entry, set ENTRY_TEMPLATE.
    if ENTRY_TEMPLATE and ENTRY_TEMPLATE not in {"auth/login.html", "login.html"}:
        # render the explicit target but still supply a form in case it needs it
        form = LoginForm() if LoginForm else None
        page = _try_render(ENTRY_TEMPLATE, form=form)
        if page:
            return page
        current_app.logger.warning(f"[entry] ENTRY_TEMPLATE='{ENTRY_TEMPLATE}' could not be rendered; redirecting to /login")
    return redirect(url_for("web.login"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm() if LoginForm else None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # simple guard-rail login to unblock UI; replace with your real auth later
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["user"] = username
            return redirect(url_for("web.dashboard"))
        flash("Invalid credentials", "error")

    # Try the common login templates with the 'form' present
    for tpl in ("auth/login.html", "login.html", "choose_login.html"):
        page = _try_render(tpl, form=form)
        if page:
            return page

    return ("<h3>Missing login templates.</h3>", 200)


@web_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("web.login"))
    for tpl in ("dashboard.html", "analytics/dashboard.html", "index.html"):
        page = _try_render(tpl)
        if page:
            return page
    return ("<h3>Missing dashboard template.</h3>", 200)


@web_bp.route("/__templates")
def __templates():
    """Quick diagnostics: show active Jinja search paths."""
    env = current_app.jinja_env
    loaders = getattr(env.loader, "loaders", [env.loader])
    lines = ["<h3>Jinja search paths</h3><ul>"]
    for l in loaders:
        for p in getattr(l, "searchpath", []):
            lines.append(f"<li>{p}</li>")
    lines.append("</ul>")
    return "\n".join(lines), 200
