# erp/web.py
from __future__ import annotations

import os
import logging
from typing import Optional

from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    url_for,
    Response,
)

log = logging.getLogger(__name__)

# Export the blueprint under the exact name app.py imports.
web_bp = Blueprint("web", __name__)

# Reasonable entry templates to try (in priority order).
ENTRY_CANDIDATES = (
    "auth/login.html",
    "choose_login.html",
    "login.html",
    "index.html",
)

# --- Jinja helpers -----------------------------------------------------------

def _template_exists(name: str) -> bool:
    """Return True if Jinja can resolve the template name."""
    try:
        # get_or_select_template resolves across all configured loaders
        current_app.jinja_env.get_or_select_template(name)
        return True
    except Exception:
        return False


def _pick_entry_template() -> Optional[str]:
    """Honor explicit ENTRY_TEMPLATE, then fall back to known candidates."""
    explicit = (current_app.config.get("ENTRY_TEMPLATE") or os.getenv("ENTRY_TEMPLATE") or "").strip()
    if explicit and _template_exists(explicit):
        return explicit

    for cand in ENTRY_CANDIDATES:
        if _template_exists(cand):
            return cand
    return None


def _safe_render(name: str) -> Response:
    """Render a template but never crash the app if that template needs context."""
    try:
        return render_template(name)
    except Exception as exc:
        # Log the real problem for operators, return a basic fallback to users.
        log.error("[templates] Unexpected error rendering %r: %s", name, exc, exc_info=True)
        return Response(
            f"<h2>Template error</h2>"
            f"<p>While rendering <code>{name}</code> we hit: <pre>{type(exc).__name__}: {exc}</pre></p>",
            mimetype="text/html",
            status=200,
        )


# Make sure '_' is defined in Jinja even if Babel isn’t wired yet.
# This prevents crashes from templates like {{ _('Login') }}.
@web_bp.record_once
def _ensure_i18n(state):
    env = state.app.jinja_env
    if "_" not in env.globals:
        env.globals["_"] = lambda s, **kwargs: s  # no-op gettext


# --- Routes ------------------------------------------------------------------

@web_bp.route("/health")
def health() -> Response:
    return {"app": "ERP-BERHAN", "status": "running"}  # lightweight health check


@web_bp.route("/")
def index():
    """
    Root: prefer the real login view if present; otherwise render the best entry template.
    Never explode on missing context variables (forms, etc.).
    """
    # If an auth blueprint exposes 'auth.login', let that view prepare its context (forms, CSRF, etc.).
    if "auth.login" in current_app.view_functions:
        return redirect(url_for("auth.login"))

    # Otherwise, try configured or discovered entry templates.
    chosen = _pick_entry_template()
    if chosen:
        return _safe_render(chosen)

    # Nothing found – return a friendly page instead of 500s.
    msg = (
        "<h2>No entry template found</h2>"
        "<p>We looked for <code>ENTRY_TEMPLATE</code> (env/config) or any of: "
        f"<code>{', '.join(ENTRY_CANDIDATES)}</code> in your configured template paths.</p>"
    )
    log.warning("[templates] No entry template resolved; check template paths and names.")
    return Response(msg, mimetype="text/html", status=200)
