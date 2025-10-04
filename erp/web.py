from flask import Blueprint, current_app, render_template, redirect, url_for, jsonify
from jinja2 import TemplateNotFound
import os

web_bp = Blueprint("web", __name__)

def _try_render(name: str):
    try:
        return render_template(name)
    except TemplateNotFound:
        current_app.logger.error(f"[templates] TemplateNotFound: missing '{name}'")
    except Exception as e:
        current_app.logger.error(f"[templates] Unexpected error rendering '{name}': {e}")
    # Last-resort fallback that never requires a WTForm
    return render_template("fallback.html")

@web_bp.get("/")
def index():
    # If auth blueprint is present, use it; otherwise fall back to the safe page
    if "auth.login" in current_app.view_functions:
        return redirect(url_for("auth.login"))
    return redirect(url_for("web.login_page"))

@web_bp.get("/login")
@web_bp.get("/auth/login")
@web_bp.get("/choose_login")
def login_page():
    entry = os.environ.get("ENTRY_TEMPLATE", "").strip() or "fallback.html"
    return _try_render(entry)

@web_bp.get("/health")
def health():
    return jsonify({"status": "ok"})
