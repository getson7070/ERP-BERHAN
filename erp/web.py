# erp/web.py
import os
from flask import Blueprint, render_template, redirect, url_for, request, session, current_app, flash
from jinja2 import TemplateNotFound, TemplateSyntaxError

# Try to use your real LoginForm if it exists; otherwise a minimal fallback.
try:
    from erp.forms.auth import LoginForm as RealLoginForm  # adjust if your path differs
    LoginForm = RealLoginForm
except Exception:
    try:
        from flask_wtf import FlaskForm
        from wtforms import StringField, PasswordField
        from wtforms.validators import DataRequired

        class LoginForm(FlaskForm):
            class Meta:
                csrf = False  # flip to True once SECRET_KEY and CSRF are ready
            username = StringField("Username", validators=[DataRequired()])
            password = PasswordField("Password", validators=[DataRequired()])
    except Exception:
        LoginForm = None  # last resort: render template without bound fields

web_bp = Blueprint("web", __name__)

ENTRY_TEMPLATE = (os.getenv("ENTRY_TEMPLATE") or "").strip()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")


def _render_safe(template_name: str, **ctx):
    try:
        return render_template(template_name, **ctx)
    except TemplateNotFound as e:
        current_app.logger.error(f"[templates] not found: '{e.name}' while rendering '{template_name}'")
    except TemplateSyntaxError as e:
        current_app.logger.error(f"[templates] syntax error in '{template_name}' line {e.lineno}: {e.message}")
    except Exception as e:
        current_app.logger.exception(f"[templates] unexpected while rendering '{template_name}': {e}")
    return None


@web_bp.route("/")
def root():
    # If ENTRY_TEMPLATE is defined, try it first, but fall back to /login.
    if ENTRY_TEMPLATE:
        page = _render_safe(ENTRY_TEMPLATE, form=(LoginForm() if LoginForm else None))
        if page:
            return page
        current_app.logger.warning(f"[entry] ENTRY_TEMPLATE='{ENTRY_TEMPLATE}' could not be rendered; falling back to /login")
    return redirect(url_for("web.login"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm() if LoginForm else None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["user"] = username
            return redirect(url_for("web.dashboard"))
        flash("Invalid credentials", "error")

    # Try the common login templates, always passing 'form'
    for tpl in (
        "auth/login.html",
        "choose_login.html",
        "login.html",
    ):
        page = _render_safe(tpl, form=form)
        if page:
            return page

    # As a last resort, show a clear diagnostic
    return (
        "<h3>ERP-BERHAN is running.</h3>"
        "<p>Expected one of: <code>templates/auth/login.html</code>, "
        "<code>templates/choose_login.html</code>, <code>templates/login.html</code>, "
        "<code>templates/index.html</code>.</p>"
        '<p>Health: <a href="/health">/health</a></p>',
        200,
    )


@web_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("web.login"))
    for tpl in ("dashboard.html", "analytics/dashboard.html", "index.html"):
        page = _render_safe(tpl)
        if page:
            return page
    return "<h3>Dashboard template not found.</h3>", 200
