"""Privacy policy page.

Simplified, framework-compatible version that does not depend on old helpers.
"""

from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("privacy", __name__)


@bp.route("/privacy")
def privacy():
    return render_template("privacy.html")
