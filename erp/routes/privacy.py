"""Routes for the privacy and compliance centre."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template

from erp.compliance.privacy import build_privacy_program_snapshot
from erp.utils import login_required

bp = Blueprint("privacy", __name__)


@bp.route("/privacy")
@login_required
def privacy_center():
    """Render the privacy program dashboard."""

    snapshot = build_privacy_program_snapshot(current_app.config)
    privacy_config = {
        "officer_email": current_app.config.get("PRIVACY_OFFICER_EMAIL"),
        "gdpr_erasure_days": current_app.config.get("GDPR_ERASURE_WINDOW_DAYS"),
        "gdpr_export_days": current_app.config.get("GDPR_EXPORT_WINDOW_DAYS"),
        "ccpa_window_days": current_app.config.get("CCPA_RESPONSE_WINDOW_DAYS"),
        "data_residency": current_app.config.get("PRIVACY_DATA_RESIDENCY"),
        "policy_version": current_app.config.get("PRIVACY_POLICY_VERSION"),
    }
    return render_template(
        "privacy.html",
        snapshot=snapshot,
        privacy_config=privacy_config,
    )
