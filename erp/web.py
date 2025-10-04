import os
from flask import Blueprint, render_template, redirect, url_for, request, session, current_app, flash
from jinja2 import TemplateNotFound, TemplateSyntaxError

try:
    from erp.forms.auth import LoginForm as RealLoginForm
    LoginForm = RealLoginForm
except Exception:
    try:
        from flask_wtf import FlaskForm
        from wtforms import StringField, PasswordField
        from wtforms.validators import DataRequired
        class LoginForm(FlaskForm):
            class Meta: csrf = False
            username = StringField("Username", validators=[DataRequired()])
            password = PasswordField("Password", validators=[DataRequired()])
    except Exception:
        LoginForm = None

web_bp = Blueprint("web", __name__)

ENTRY_TEMPLATE = (os.getenv("ENTRY_TEMPLATE") or "").strip()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

def _render_safe(name: str, **ctx):
    try:
        return render_template(name, **ctx)
    except TemplateNotFound as e:
        current_app.logger.error(f"[templates] not found: {e.name} (asked for {name})")
    except TemplateSyntaxError as e:
        current_app.logger.error(f"[templates] syntax error in {name}:{e.lineno} {e.message}")
    except Exception as e:
        current_app.logger.exception(f"[templates] unexpected for {name}: {e}")
    return None

@web_bp.route("/")
def root():
    if ENTRY_TEMPLATE:
        page = _render_safe(ENTRY_TEMPLATE, form=(LoginForm() if LoginForm else None))
        if page: return page
    return redirect(url_for("web.login"))

@web_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm() if LoginForm else None
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["user"] = ADMIN_USER
            return redirect(url_for("web.dashboard"))
        flash("Invalid credentials", "error")
    for tpl in ("auth/login.html", "choose_login.html", "login.html", "index.html"):
        page = _render_safe(tpl, form=form)
        if page: return page
    return (
        "<h3>ERP-BERHAN is running.</h3>"
        "Expected one of: <code>templates/auth/login.html</code>, "
        "<code>templates/choose_login.html</code>, <code>templates/login.html</code>, "
        "<code>templates/index.html</code>.<br/>"
        'Health: <a href="/health">/health</a>', 200
    )

@web_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("web.login"))
    for tpl in ("dashboard.html", "analytics/dashboard.html", "index.html"):
        page = _render_safe(tpl)
        if page: return page
    return "<h3>No dashboard template found.</h3>", 200
